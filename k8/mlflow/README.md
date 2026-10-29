# MLflow Tracking Server

MLflow runs in Kubernetes and uses PostgreSQL for its backend metadata store and AWS S3 for experiment artifacts.

## Database

MLflow uses the `mlflow` database on the existing PostgreSQL service.

- PostgreSQL service: `postgres`
- Database: `mlflow`
- Database role: `airflow`
- Kubernetes Secret: `weather-env`

The existing `airflow` database remains dedicated to Airflow metadata.

## Create the database

Run the following command **on the Oracle VM**, from the repository root, after the SQL script is available there:

```bash
sudo k3s kubectl exec -i postgres-0 -n default -- \
  psql -U airflow -d postgres \
  < k8/postgres/create_mlflow_database.sql
```

The script creates the `mlflow` database only if it does not already exist. It requires a PostgreSQL role permitted to create databases.

## Configuration

The `weather-env` Kubernetes Secret must contain:

- `MLFLOW_DB_USER`
- `MLFLOW_DB_PASSWORD`
- `MLFLOW_DB_HOST`
- `MLFLOW_DB_PORT`
- `MLFLOW_DB_NAME`
- `S3_BUCKET_NAME`
- `MLFLOW_S3_PREFIX`

Set `MLFLOW_DB_NAME=mlflow`. Keep `POSTGRES_DB=airflow` so the existing Airflow configuration remains unchanged.

Do not commit `.k8-env` or other files containing secret values.

## Deploy and verify

Apply the MLflow deployment and service manifests using the project's deployment workflow.

Verify that:

1. The `mlflow-tracking` deployment rolls out successfully.
2. The MLflow pod reaches `Running` and is ready.
3. The startup logs contain no database migration errors.
4. The MLflow health endpoint returns `OK`.
