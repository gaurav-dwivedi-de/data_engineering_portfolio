from datetime import datetime, timedelta

import os
import subprocess
import sys
from uuid import uuid4

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

from orchestration.check_archive import (
    determine_pipeline_branch,
    run_w1_w2_w3,
    archive_expired_forecasts,
)

from orchestration.create_db import create_table
from orchestration.cloud_storage import (
    upload_airflow_artifacts,
    upload_p2_w7_artifacts,
    upload_sklearn_candidate,
    upload_spark_candidate,
)


# =====================================================
# DEFAULT ARGUMENTS
# =====================================================

default_args = {
    "owner": "portfolio_user",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# =====================================================
# PROJECT PATHS
# =====================================================

W4_PATH = "/opt/airflow/w4"
W5_PATH = "/opt/airflow/w5"
W6_PATH = "/opt/airflow/w6"
W7_PATH = "/opt/airflow/w7"
W8_PATH = "/opt/airflow/w8"
W9_PATH = "/opt/airflow/w9"
P2_W7_PATH = "/opt/airflow/p2_w7_spark_mllib"
MLFLOW_PATH = "/opt/airflow/mlflow_integration"


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def create_project_task(
    task_id: str,
    project_dir: str,
    module: str,
):
    """
    Execute an independent project using its main module.
    """

    return BashOperator(
        task_id=task_id,
        bash_command=f"""
        set -e
        cd {project_dir}
        python -m {module}
        """,
    )


def run_candidate_pipeline(
    project_dir: str,
    module: str,
    candidate_type: str,
):
    """
    Execute a model candidate pipeline with a unique candidate ID.

    Upload candidate artifacts to S3 after successful training.
    Return the candidate ID to Airflow through XCom.
    """

    candidate_run_id = uuid4().hex

    env = os.environ.copy()
    env["CANDIDATE_RUN_ID"] = candidate_run_id

    print(f"[CANDIDATE] Project: {project_dir}")
    print(f"[CANDIDATE] Candidate Type: {candidate_type}")
    print(f"[CANDIDATE] Candidate Run ID: {candidate_run_id}")

    subprocess.run(
        [sys.executable, "-m", module],
        cwd=project_dir,
        env=env,
        check=True,
    )

    print(
        f"[CANDIDATE] Pipeline completed: {candidate_run_id}"
    )

    if candidate_type == "sklearn":
        upload_sklearn_candidate(candidate_run_id)

    elif candidate_type == "spark":
        upload_spark_candidate(candidate_run_id)

    else:
        raise ValueError(
            f"Unsupported candidate type: {candidate_type}"
        )

    print(
        f"[CANDIDATE] Artifacts uploaded to S3: {candidate_run_id}"
    )

    return candidate_run_id

def run_mlflow_candidate_evaluation(**context):
    """
    Evaluate W8 and P2-W7 candidates against their registered champions.

    Candidate IDs are retrieved from the upstream Airflow tasks through XCom.
    """

    ti = context["ti"]

    sklearn_candidate_run_id = ti.xcom_pull(
        task_ids="run_w8_pipeline"
    )

    spark_candidate_run_id = ti.xcom_pull(
        task_ids="run_p2_w7_mllib_pipeline"
    )

    if not sklearn_candidate_run_id or not spark_candidate_run_id:
        raise ValueError(
            "Missing candidate IDs from W8 or P2-W7 XCom."
        )

    print(
        f"[MLFLOW] Sklearn candidate: {sklearn_candidate_run_id}"
    )
    print(
        f"[MLFLOW] Spark candidate: {spark_candidate_run_id}"
    )

    command = [
        sys.executable,
        "-m",
        "src.evaluate_models",
        "--evaluate-candidates",
        "--sklearn-candidate-run-id",
        sklearn_candidate_run_id,
        "--spark-candidate-run-id",
        spark_candidate_run_id,
    ]

    subprocess.run(
        command,
        cwd=MLFLOW_PATH,
        env=os.environ.copy(),
        check=True,
    )

    print("[MLFLOW] Candidate evaluation completed.")

def end_pipeline():
    """
    Final pipeline message.
    """

    print("\n============================================")
    print("Weather Intelligence Platform Completed")
    print("============================================\n")


def refresh_applications():
    """
    Restart FastAPI and Prediction Dashboard deployments
    when running in Kubernetes.

    Skip application refresh when running under Docker Compose.
    """

    import os
    from datetime import datetime, timezone

    # Kubernetes automatically provides this variable
    # to containers running inside the cluster.
    if not os.getenv("KUBERNETES_SERVICE_HOST"):
        print(
            "[REFRESH] Docker Compose environment detected. "
            "Application refresh skipped."
        )
        return

    from kubernetes import client, config

    # Load Kubernetes credentials from inside the Airflow pod.
    config.load_incluster_config()

    apps = client.AppsV1Api()

    deployments = [
        "fastapi-deployment",
        "prediction-dashboard-deployment",
    ]

    for deployment_name in deployments:
        deployment = apps.read_namespaced_deployment(
            name=deployment_name,
            namespace="default",
        )

        annotations = (
            deployment.spec.template.metadata.annotations or {}
        )

        annotations["kubectl.kubernetes.io/restartedAt"] = (
            datetime.now(timezone.utc).isoformat()
        )

        deployment.spec.template.metadata.annotations = annotations

        apps.patch_namespaced_deployment(
            name=deployment_name,
            namespace="default",
            body=deployment,
        )

        print(
            f"[REFRESH] Restart triggered: {deployment_name}"
        )


# =====================================================
# DAG
# =====================================================

with DAG(
    dag_id="weather_etl_pipeline",
    description="Weather Intelligence Platform",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    
    max_active_runs=1,
    max_active_tasks=1,
    catchup=False,
    default_args=default_args,
    tags=[
        "portfolio",
        "weather",
        "etl",
        "spark",
        "ml",
        "mlops",
    ],
) as dag:

    # =================================================
    # DATABASE INITIALIZATION
    # =================================================

    create_database_task = PythonOperator(
        task_id="create_postgresql_table",
        python_callable=create_table,
    )

    # =================================================
    # PIPELINE RECOVERY CHECK
    # =================================================

    @task.branch(task_id="check_pipeline_state")
    def check_pipeline_state():
        return determine_pipeline_branch()

    pipeline_check = check_pipeline_state()

    # =================================================
    # RECOVERY TASKS
    # =================================================

    run_all_recovery = PythonOperator(
        task_id="run_w1_w2_w3",
        python_callable=run_w1_w2_w3,
    )

    skip_recovery = EmptyOperator(
        task_id="skip_recovery",
    )

    recovery_complete = EmptyOperator(
        task_id="recovery_complete",
        trigger_rule="none_failed_min_one_success",
    )

    # =================================================
    # FORECAST -> ARCHIVE TRANSITION
    # =================================================

    archive_forecast_transition = PythonOperator(
        task_id="archive_expired_forecasts",
        python_callable=archive_expired_forecasts,
    )

    # =================================================
    # WEEK 4
    # =================================================

    run_w4_pipeline = create_project_task(
        task_id="run_w4_pipeline",
        project_dir=W4_PATH,
        module="src.main",
    )

    # =================================================
    # WEEK 5
    # =================================================

    run_w5_pipeline = create_project_task(
        task_id="run_w5_pipeline",
        project_dir=W5_PATH,
        module="weather_etl.main",
    )

    # =================================================
    # WEEK 6
    # =================================================

    run_w6_pipeline = create_project_task(
        task_id="run_w6_pipeline",
        project_dir=W6_PATH,
        module="src.main",
    )

    # =================================================
    # WEEK 7
    # =================================================

    run_w7_pipeline = create_project_task(
        task_id="run_w7_pipeline",
        project_dir=W7_PATH,
        module="src.main",
    )

    # =================================================
    # WEEK 8
    # =================================================

    run_w8_pipeline = PythonOperator(
        task_id="run_w8_pipeline",
        python_callable=run_candidate_pipeline,
        op_kwargs={
            "project_dir": W8_PATH,
            "module": "src.main",
            "candidate_type": "sklearn",
        },
    )

    # =================================================
    # WEEK 9
    # =================================================

    run_w9_pipeline = create_project_task(
        task_id="run_w9_pipeline",
        project_dir=W9_PATH,
        module="src.main",
    )

    upload_prediction_to_minio = create_project_task(
        task_id="upload_prediction_to_minio",
        project_dir=W9_PATH,
        module="src.upload_to_minio",
    )


    # =================================================
    # P2-W7 — SPARK MLLIB
    # =================================================

    run_p2_w7_mllib_pipeline = PythonOperator(
        task_id="run_p2_w7_mllib_pipeline",
        python_callable=run_candidate_pipeline,
        op_kwargs={
            "project_dir": P2_W7_PATH,
            "module": "src.main",
            "candidate_type": "spark",
        },
    )

    # =================================================
    # MLflow Integration
    # =================================================

    ensure_initial_mlflow_baselines = BashOperator(
    task_id="ensure_initial_mlflow_baselines",
    bash_command="""
        set -e

        cd /opt/airflow/mlflow_integration

        check_baselines() {
            python - <<'PY'
import sys

sys.path.insert(0, "/opt/airflow/mlflow_integration/src")

from config import MLFLOW_TRACKING_URI
from register_initial_models import baselines_already_initialized
from mlflow.tracking import MlflowClient

client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

try:
    initialized = baselines_already_initialized(client)
except Exception as exc:
    print(f"MLflow baseline check failed: {exc}")
    sys.exit(2)

print(f"Initial MLflow baselines initialized: {initialized}")
sys.exit(0 if initialized else 1)
PY
        }

        if check_baselines; then
            echo "Initial baselines are valid. Skipping bootstrap."
        else
            result=$?

            if [ "$result" -eq 1 ]; then
                echo "Initial baselines are missing or invalid."

                python -m src.evaluate_models --log-mlflow

                python /opt/airflow/mlflow_integration/src/register_initial_models.py

                echo "Verifying baseline registration..."
                check_baselines
            else
                echo "Unable to inspect MLflow registry. Stopping."
                exit 1
            fi
        fi
    """,
)

    run_mlflow_evaluation = PythonOperator(
        task_id="run_mlflow_evaluation",
        python_callable=run_mlflow_candidate_evaluation,
    )

    # =================================================
    # MLflow — PRODUCTION CHAMPION VERIFICATION
    # =================================================

    verify_production_champion = BashOperator(
        task_id="verify_production_champion",
        bash_command="""
            set -e

            cd /opt/airflow/mlflow_integration

            python - <<'PY'
import mlflow
from mlflow.tracking import MlflowClient

from src.config import MLFLOW_TRACKING_URI
from src.registration import (
    GLOBAL_PRODUCTION_MODEL,
    GLOBAL_CHAMPION_ALIAS,
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

client = MlflowClient(
    tracking_uri=MLFLOW_TRACKING_URI
)

print("[MLFLOW] Verifying global production model...")

registered_model = client.get_registered_model(
    GLOBAL_PRODUCTION_MODEL
)

champion = client.get_model_version_by_alias(
    GLOBAL_PRODUCTION_MODEL,
    GLOBAL_CHAMPION_ALIAS,
)

if champion.status != "READY":
    raise RuntimeError(
        f"Production champion is not READY: {champion.status}"
    )

tags = champion.tags or {}

if tags.get("registration_type") != "global_production":
    raise RuntimeError(
        "The champion is not tagged as a global production model."
    )

if champion.name != GLOBAL_PRODUCTION_MODEL:
    raise RuntimeError(
        "The champion belongs to an unexpected registered model."
    )

print("[MLFLOW] Production champion verified.")
print(f"[MLFLOW] Model: {registered_model.name}")
print(f"[MLFLOW] Alias: {GLOBAL_CHAMPION_ALIAS}")
print(f"[MLFLOW] Version: {champion.version}")
print(f"[MLFLOW] Status: {champion.status}")
PY
        """,
    )

    # =================================================
    # CLOUD STORAGE
    # =================================================

    upload_artifacts_to_s3 = PythonOperator(
        task_id="upload_artifacts_to_s3",
        python_callable=upload_airflow_artifacts,
    )

    upload_p2_w7_artifacts_to_s3 = PythonOperator(
        task_id="upload_p2_w7_artifacts_to_s3",
        python_callable=upload_p2_w7_artifacts,
    )

    # =================================================
    # REFRESH APPLICATIONS
    # =================================================

    refresh_applications_task = PythonOperator(
        task_id="refresh_applications",
        python_callable=refresh_applications,
    )

    # =================================================
    # END PIPELINE
    # =================================================

    end_task = PythonOperator(
        task_id="end_pipeline",
        python_callable=end_pipeline,
    )

    # =================================================
    # PIPELINE FLOW
    # =================================================

    # Database must exist before archive checking.
    create_database_task >> pipeline_check

    # -------------------------------------------------
    # Recovery branch
    # -------------------------------------------------

    pipeline_check >> run_all_recovery
    pipeline_check >> skip_recovery

    run_all_recovery >> recovery_complete
    skip_recovery >> recovery_complete

    # -------------------------------------------------
    # Forecast -> Archive transition
    #
    # ALWAYS runs after recovery/skip and before W4.
    # -------------------------------------------------

    recovery_complete >> archive_forecast_transition

    # -------------------------------------------------
    # Main pipeline
    # -------------------------------------------------

    (
        archive_forecast_transition
        >> run_w4_pipeline
        >> run_w5_pipeline
        >> run_w6_pipeline
        >> run_w7_pipeline
        >> ensure_initial_mlflow_baselines
        >> run_w8_pipeline
        >> run_p2_w7_mllib_pipeline
        >> upload_p2_w7_artifacts_to_s3
        >> run_mlflow_evaluation
        >> verify_production_champion
        >> run_w9_pipeline
        >> upload_artifacts_to_s3
        >> upload_prediction_to_minio
        >> refresh_applications_task
        >> end_task
    )