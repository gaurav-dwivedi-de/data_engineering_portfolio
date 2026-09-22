# Weather Intelligence Platform

An end-to-end weather data engineering and MLOps platform that turns Open-Meteo weather data into cleaned datasets, PostgreSQL records, Spark/Parquet outputs, machine-learning artifacts, batch predictions, a FastAPI prediction service, and interactive Plotly Dash dashboards.

The repository is structured as a progressive W1–W10 portfolio build and includes a Phase 2 production layer using Docker, Airflow, Kubernetes/K3s, MinIO, AWS S3, GitHub Actions, GHCR, and Oracle Cloud.

## What the platform does

- Collects historical and forecast weather data for London, Manchester, and Edinburgh.
- Cleans, validates, transforms, and stores weather data for downstream processing.
- Loads structured data into PostgreSQL.
- Runs the daily pipeline through an Apache Airflow DAG.
- Processes weather data with PySpark and writes Parquet datasets.
- Publishes data and ML artifacts to MinIO/S3-compatible storage and AWS S3.
- Engineers temporal, rolling, lag, delta, percentage-change, and city features.
- Compares Linear Regression and Random Forest models using MAE, RMSE, and R².
- Produces a selected model, scaler, metrics, figures, and batch predictions.
- Serves next-hour temperature predictions through FastAPI.
- Presents historical and live predictions through Plotly Dash.
- Runs locally with Docker Compose or in Kubernetes/K3s with persistent PostgreSQL and MinIO storage.

## Architecture

```text
Open-Meteo API / historical CSVs
              │
              ▼
W1 cleaning → W2 ETL → W3 PostgreSQL
                              │
                              ▼
                    W4 Airflow DAG (@daily)
                              │
                              ▼
                  W5 PySpark transformation
                              │
                              ▼
                    W6 MinIO / Parquet data
                              │
                              ▼
                  W7 feature engineering
                              │
                              ▼
                  W8 model training/evaluation
                              │
                              ▼
                       W9 batch prediction
                              │
                 ┌────────────┴───────���────┐
                 ▼                         ▼
          AWS S3 artifacts          W10 application layer
                                  ┌──────────┴──────────┐
                                  ▼                     ▼
                             FastAPI API          Plotly Dash
```

`dags/weather_etl_dag.py` is the control flow for the production pipeline. It initializes PostgreSQL, evaluates recovery state, runs the W4–W9 modules, uploads prediction and model artifacts, and refreshes the FastAPI and dashboard deployments when running inside Kubernetes.

## Technology stack

- **Language:** Python 3.11
- **Orchestration:** Apache Airflow 3.3, Python/Bash operators, task branching
- **Data processing:** Pandas, PySpark 4.0, PyArrow, Parquet
- **Storage:** PostgreSQL 16, MinIO, AWS S3, Kubernetes PersistentVolumeClaims
- **Machine learning:** scikit-learn, Joblib, Matplotlib
- **Application:** FastAPI, Uvicorn, Pydantic, Plotly Dash
- **Infrastructure:** Docker, Docker Compose, Kubernetes, K3s, Oracle Cloud
- **Delivery:** GitHub Actions, Docker Buildx, QEMU, GitHub Container Registry

## Repository structure

```text
data_engineering_portfolio/
├── dags/                         Airflow DAG definitions
├��─ orchestration/                Recovery, database, and S3 orchestration helpers
├── tests/                        Repository-level import tests
├── k8/                           Kubernetes manifests for platform workloads
│   ├── airflow/                  Airflow API server, scheduler, DAG processor, init, RBAC
│   ├── dashboard/                Prediction dashboard Deployment and Service
│   ├── fastapi/                  FastAPI Deployment and Service
│   ├── minio/                    MinIO StatefulSet, Service, and PVC
│   └── postgres/                 PostgreSQL StatefulSet, Service, and PVC
├── w1_weather_data_cleaner/      Historical data cleaning and exploratory analysis
├── w2_weather_etl_pipeline/      Extract, transform, validate, and load ETL
├── w3_postgresql_loader/         PostgreSQL schema creation, loading, and validation
├── w4_airflow_weather_pipeline/  Forecast extraction and ETL implementation
├── w5_spark_weather_etl/         PySpark extract, transform, analysis, and Parquet load
├── w6_dashboard_minio/           MinIO upload/download and weather dashboard
├── w7_feature_engineering/       ML feature dataset generation
├── w8_weather_prediction_model/  Model comparison, evaluation, and artifact creation
├── w9_ml_pipeline/               Model loading, batch prediction, evaluation, and upload
├── w10_fastapi_service/          FastAPI prediction API and Plotly Dash application
├── Dockerfile                    Canonical Airflow-based project image
├── docker-compose.yml             Local PostgreSQL, MinIO, Airflow, API, and dashboards
├── requirements.txt               Full local/development dependency set
├── docker_requirements.txt        Dependencies installed into the image
└── .github/workflows/ci.yml       Validation, multi-platform build, and K3s deployment
```

## Data and ML artifacts

The pipeline produces and exchanges the following artifacts:

| Artifact | Purpose |
|---|---|
| `w7_features_final.parquet` | ML-ready feature dataset |
| `best_model.pkl` | Selected trained prediction model |
| `scaler.pkl` | Feature scaling transformer used by the model |
| `model_metrics.json` | Selected model name, MAE, RMSE, R², and training metadata |
| `weather_predictions.csv` | Batch prediction output |

AWS S3 uses these logical keys:

```text
features/w7_features_final.parquet
models/best_model.pkl
models/scaler.pkl
models/model_metrics.json
predictions/weather_predictions.csv
```

`orchestration/cloud_storage.py` uploads the W7–W9 artifacts using `AWS_REGION` and `S3_BUCKET_NAME`. The deployed Kubernetes application workloads use the `weather-env` Secret to obtain their configuration and download current artifacts during startup.

## Local development with Docker Compose

### Prerequisites

- Docker and Docker Compose
- Git
- At least the resources required to run PostgreSQL, MinIO, Airflow, Spark, FastAPI, and Dash together

Create a local `.env` file before starting Compose. The Compose file expects PostgreSQL settings and dashboard configuration, and the pipeline's cloud-upload path additionally requires AWS configuration when used:

```dotenv
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow
POSTGRES_PORT=5432
W6_DASH_PORT=8050
AWS_REGION=eu-west-2
S3_BUCKET_NAME=your-bucket-name
```

Do not commit real credentials, AWS keys, Kubernetes secrets, or SSH private keys.

### Build and start the platform

```bash
git clone https://github.com/gaurav-dwivedi-de/data_engineering_portfolio.git
cd data_engineering_portfolio

# Build the canonical image and start the local platform
docker compose build
docker compose up -d

# Inspect service status and logs
docker compose ps
docker compose logs -f airflow-apiserver
```

The local Compose services expose:

| Service | Address | Purpose |
|---|---|---|
| Airflow API server | `http://localhost:8080` | DAG management and monitoring |
| FastAPI | `http://localhost:8000` | Prediction API |
| FastAPI health endpoint | `http://localhost:8000/api` | API status check |
| FastAPI Swagger UI | `http://localhost:8000/docs` | Interactive API documentation |
| Prediction Dashboard | `http://localhost:8051` | W10 historical/live prediction UI |
| MinIO API | `http://localhost:9000` | Object storage API |
| MinIO console | `http://localhost:9001` | Object storage administration |
| PostgreSQL | `localhost:5432` | Relational data store |

The Compose initialization creates the Airflow database and an `admin` Airflow user. Change the development credentials before using the platform outside a local environment.

### Run the import tests

```bash
python -m unittest tests/test_project_imports.py
```

The current repository-level test checks that the core numerical, data, and ML dependencies import successfully. Component and end-to-end testing remains part of the planned Phase 2 testing work.

## Running individual stages

Each stage has a Python module entry point used by Airflow. From the corresponding directory, the main processing stages can be run as follows:

```bash
python -m src.main                  # W4, W6, or W7 when run from that module directory
python -m weather_etl.main          # W5
python -m src.main                  # W8 and W9 when run from that module directory
python -m app.main                  # Import target for the FastAPI application
python -m dashboard.app             # W10 Plotly Dash application
```

For the exact working directory and data paths, use the README and configuration files inside each W1–W10 module. The Airflow DAG is the recommended way to run the complete sequence because it supplies the container paths and stage dependencies.

## Airflow pipeline

The DAG ID is `weather_etl_pipeline`, scheduled daily with catchup disabled and one active run/task at a time. Its main dependency chain is:

```text
create_postgresql_table
  → check_pipeline_state
  → recovery or skip_recovery
  → archive_expired_forecasts
  → W4
  → W5
  → W6
  → W7
  → W8
  → W9
  → upload_prediction_to_minio
  → upload_artifacts_to_s3
  → refresh_applications
  → end_pipeline
```

The recovery branch uses `orchestration/check_archive.py`; database setup is handled by `orchestration/create_db.py`; cloud artifact publication is handled by `orchestration/cloud_storage.py`.

## FastAPI prediction API

The W10 service defines:

- `GET /api` — returns an online health response.
- `POST /predict` — validates the feature payload with `PredictionRequest` and returns `predicted_temperature`.

The request schema includes weather observations, calendar fields, rolling means, lag/delta features, city indicators, and the forecast-source indicator. The predictor loads the trained model and scaler through the W10 application modules.

Example health request:

```bash
curl http://localhost:8000/api
```

Use `http://localhost:8000/docs` to inspect the generated OpenAPI schema and construct a complete `/predict` request from the checked-in Pydantic schema.

## Kubernetes and cloud deployment

The `k8/` manifests deploy the platform to Kubernetes/K3s:

- PostgreSQL and MinIO run as StatefulSets with persistent volumes.
- Airflow runs as an API server, scheduler, DAG processor, and initialization Job.
- FastAPI and the prediction dashboard run as Deployments with Services.
- `k8/ingress.yaml` defines the platform ingress.
- Workloads reference the external `weather-env` Secret.

For a manually prepared cluster, apply the manifests in dependency order:

```bash
kubectl apply -f k8/postgres/
kubectl apply -f k8/minio/
kubectl apply -f k8/airflow/
kubectl apply -f k8/fastapi/
kubectl apply -f k8/dashboard/
kubectl apply -f k8/ingress.yaml

kubectl get pods
kubectl get statefulsets
kubectl get deployments
```

The production workflow targets an Oracle Cloud ARM64 VM running K3s. It preserves PostgreSQL and MinIO PVCs during normal deployments and uses commit-SHA image tags rather than `latest`.

## CI/CD

`.github/workflows/ci.yml` runs on pushes to `main` and pull requests. It:

1. Detects deployable changes, including Python, Docker, dependency, Compose, and Kubernetes files.
2. Installs Python 3.11 and limited CI dependencies.
3. Verifies the expected repository structure.
4. Runs `tests/test_project_imports.py`.
5. Builds and publishes `linux/amd64` and `linux/arm64` images to GHCR for qualifying pushes.
6. Connects to the Oracle K3s host using GitHub Actions secrets.
7. Applies PostgreSQL, MinIO, Airflow, FastAPI, dashboard, and ingress resources in order.
8. Waits for workload rollouts and prints the deployed image versions.

Images are published as:

```text
ghcr.io/gaurav-dwivedi-de/data_engineering_portfolio:<commit-sha>
```

Required deployment secrets include `ORACLE_HOST`, `ORACLE_USER`, and `ORACLE_SSH_KEY`. AWS and Kubernetes secret values must remain outside the repository.

## Project status

### Complete

- W1–W10 weather data, ML, API, and dashboard flow.
- Kubernetes foundation and platform consolidation.
- Oracle Cloud/K3s deployment.
- PostgreSQL and MinIO persistent storage.
- Initial CI validation and repository checks.
- GHCR integration with immutable commit-SHA image tags.
- Multi-platform AMD64/ARM64 image builds.
- Automated K3s workload deployment.

### In progress or planned

- P2-W4 rollback and recovery validation.
- P2-W5 public deployment, DNS, ingress, TLS, and Cloudflare integration.
- P2-W6 MLflow experiment and model lifecycle tracking.
- P2-W7 comprehensive component, integration, data-quality, and end-to-end testing.
- P2-W8 monitoring, lineage verification, and final platform integration.

## Security notes

- Keep `.env` files, AWS credentials, Kubernetes Secret values, database passwords, and SSH keys out of Git.
- Replace development defaults before any shared or public deployment.
- Review Kubernetes resource access and ingress exposure before making services public.

## License

No license file is currently defined in the repository. Add an appropriate license before distributing the project for reuse.
