#!/usr/bin/env bash
set -Eeuo pipefail

readonly REPO="/home/ubuntu/data_engineering_portfolio"
readonly KUBECTL=(sudo k3s kubectl)

: "${IMAGE_TAG:?IMAGE_TAG must be set}"

if [[ ! "$IMAGE_TAG" =~ ^[a-f0-9]{40}$ ]]; then
  echo "ERROR: IMAGE_TAG must be a full Git commit SHA." >&2
  exit 1
fi

trap 'status=$?; echo "ERROR: Deployment failed (exit $status, line $LINENO)." >&2; exit "$status"' ERR

cd "$REPO"

echo "Synchronizing repository to image commit..."
git fetch origin main
git checkout --detach "$IMAGE_TAG"
git log -1 --oneline

echo "Checking Kubernetes Secret..."
"${KUBECTL[@]}" get secret weather-env >/dev/null

echo "1. Deploying PostgreSQL..."
"${KUBECTL[@]}" apply -f "$REPO/k8/postgres/pvc.yaml"
"${KUBECTL[@]}" apply -f "$REPO/k8/postgres/statefulset.yaml"
"${KUBECTL[@]}" apply -f "$REPO/k8/postgres/service.yaml"
"${KUBECTL[@]}" rollout status statefulset/postgres --timeout=180s

echo "Initializing MLflow database..."
"${KUBECTL[@]}" exec -i postgres-0 -n default -- \
  psql -U airflow -d postgres \
  < "$REPO/k8/postgres/create_mlflow_database.sql"

echo "Verifying MLflow database..."
"${KUBECTL[@]}" exec postgres-0 -n default -- \
  psql -U airflow -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname = 'mlflow'" \
  | grep -qx '1'

echo "2. Deploying MinIO..."
"${KUBECTL[@]}" apply -f "$REPO/k8/minio/pvc.yaml"
"${KUBECTL[@]}" apply -f "$REPO/k8/minio/statefulset.yaml"
"${KUBECTL[@]}" apply -f "$REPO/k8/minio/service.yaml"
"${KUBECTL[@]}" rollout status statefulset/weather-minio --timeout=180s

echo "3. Initializing Airflow..."
"${KUBECTL[@]}" delete job airflow-init --ignore-not-found=true

sed "s|INIT_IMAGE_TAG|${IMAGE_TAG}|g" "$REPO/k8/airflow/airflow-init.yaml" \
  | "${KUBECTL[@]}" apply -f -

"${KUBECTL[@]}" wait --for=condition=complete job/airflow-init --timeout=300s

echo "4. Deploying Airflow..."
for component in api-server scheduler dag-processor; do
  sed "s|IMAGE_TAG|${IMAGE_TAG}|g" "$REPO/k8/airflow/${component}.yaml" \
    | "${KUBECTL[@]}" apply -f -
done

"${KUBECTL[@]}" rollout status deployment/airflow-apiserver --timeout=180s
"${KUBECTL[@]}" rollout status deployment/airflow-scheduler --timeout=180s
"${KUBECTL[@]}" rollout status deployment/airflow-dag-processor --timeout=180s

echo "5. Deploying FastAPI..."
sed "s|IMAGE_TAG|${IMAGE_TAG}|g" "$REPO/k8/fastapi/deployment.yaml" \
  | "${KUBECTL[@]}" apply -f -
"${KUBECTL[@]}" apply -f "$REPO/k8/fastapi/service.yaml"
"${KUBECTL[@]}" rollout status deployment/fastapi-deployment --timeout=180s

echo "6. Deploying Dashboard..."
sed "s|IMAGE_TAG|${IMAGE_TAG}|g" "$REPO/k8/dashboard/deployment.yaml" \
  | "${KUBECTL[@]}" apply -f -
"${KUBECTL[@]}" apply -f "$REPO/k8/dashboard/service.yaml"
"${KUBECTL[@]}" rollout status deployment/prediction-dashboard-deployment --timeout=180s

echo "7. Deploying MLflow..."
echo "Manifest: $REPO/k8/mlflow/deployment.yaml"
echo "Image tag: $IMAGE_TAG"

sed "s|IMAGE_TAG|${IMAGE_TAG}|g" "$REPO/k8/mlflow/deployment.yaml" \
  > /tmp/mlflow-deployment-rendered.yaml

echo "Rendered MLflow manifest:"
nl -ba /tmp/mlflow-deployment-rendered.yaml

"${KUBECTL[@]}" apply -f /tmp/mlflow-deployment-rendered.yaml
"${KUBECTL[@]}" apply -f "$REPO/k8/mlflow/service.yaml"
"${KUBECTL[@]}" rollout status deployment/mlflow-tracking --timeout=180s

echo "8. Applying Kubernetes Ingress..."
"${KUBECTL[@]}" apply -f "$REPO/k8/ingress.yaml"
"${KUBECTL[@]}" get ingress weather-platform-ingress

echo "Final deployment status..."
"${KUBECTL[@]}" get statefulsets
"${KUBECTL[@]}" get deployments
"${KUBECTL[@]}" get jobs
"${KUBECTL[@]}" get pods
"${KUBECTL[@]}" get deployments \
  -o custom-columns='NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image'

echo "All workloads deployed successfully."
