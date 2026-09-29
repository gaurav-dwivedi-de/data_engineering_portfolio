# Weather Intelligence Platform

An end-to-end data engineering and machine learning platform for processing weather data, orchestrating the complete data pipeline, generating ML-ready features, training prediction models, and serving predictions via FastAPI.

The project began as a 12-week data engineering and ML build and has been extended into a cloud-native platform using Docker, Kubernetes, Oracle Cloud, GitHub Actions, and GitHub Container Registry.

---

## Overview

The platform covers the complete data and machine learning lifecycle:

- Weather data collection and cleaning
- ETL processing
- PostgreSQL data storage
- Apache Airflow workflow orchestration
- PySpark data processing
- MinIO / S3-compatible object storage
- Feature engineering (transforming weather data into ML-ready features)
- Machine learning model training and evaluation
- Batch prediction
- FastAPI prediction service
- Interactive weather prediction Dashboard
- Docker containerisation
- Kubernetes deployment
- Oracle Cloud K3s deployment
- GitHub Actions CI/CD
- GitHub Container Registry (GHCR)
- Immutable commit-SHA container images
- Automated deployment from GitHub to Oracle K3s
- Persistent storage for PostgreSQL and MinIO

The platform is designed around the following development and deployment workflow:

```
Local Change
    ↓
Local Testing
    ↓
GitHub Desktop
    ↓
GitHub
    ↓
GitHub Actions
    ↓
Validation + Tests
    ↓
Multi-platform Docker Build
    ↓
GitHub Container Registry
    ↓
Oracle Cloud K3s
    ↓
Kubernetes Rollout
    ↓
Updated Platform
```

---

# Architecture

## Data Engineering and ML Pipeline

Apache Airflow is the central orchestration layer for the W1-W10 pipeline. It coordinates the processing stages and the movement of data and artifacts between the processing, database, and object storage layers.

PostgreSQL and MinIO are infrastructure services used by the pipeline. They are deployed and managed as Kubernetes workloads, while Airflow orchestrates the pipeline tasks that use those services.

```
                     WEATHER DATA
                          │
                          ▼
             ┌────────────���───────────┐
             │ W1 — Data Collection & │
             │      Cleaning          │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W2 — ETL Pipeline      │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W3 — PostgreSQL Loader │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W4 — Airflow           │
             │      Orchestration     │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W5 — PySpark ETL       │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W6 — MinIO / S3        │
             │      + Dashboard Data  │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W7 — Feature           │
             │      Engineering       │
             │ (ML-ready features)    │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W8 — ML Model Training │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W9 — Batch Prediction  │
             └───────────┬────────────┘
                         ▼
             ┌────────────────────────┐
             │ W10 — FastAPI +        │
             │       Dashboard        │
             └────────────────────────┘
```

### Airflow's Role

Airflow is not only responsible for the FastAPI and Dashboard layer. It acts as the **central workflow orchestrator** for the full W1-W10 processing pipeline.

In simple terms:

```
Airflow
│
├── Coordinates data ingestion and cleaning
├── Coordinates ETL processing
├── Coordinates PostgreSQL loading
├── Coordinates PySpark processing
├── Coordinates object-storage operations
├── Coordinates feature engineering
├── Coordinates ML processing
├── Coordinates batch prediction
└── Produces / prepares outputs consumed by
    FastAPI and the Dashboard
```

PostgreSQL and MinIO themselves run as persistent Kubernetes services. Airflow coordinates the pipeline tasks that create, process, load, read, and publish the required data and artifacts.

---

# Production / Cloud Architecture

Phase 2 adds a production engineering layer around the original W1-W10 platform.

```
                LOCAL DEVELOPMENT
                       │
                       ▼
                GitHub Desktop
                       │
                       ▼
                     GitHub
                       │
                       ▼
                GitHub Actions
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Changes       Tests       Docker Build
       Detection    + Validation
          │            │            │
          └────────────┼────────────┘
                       ▼
             Multi-platform Image
                AMD64 + ARM64
                       │
                       ▼
                      GHCR
                       │
                       ▼
              Oracle Cloud VM
                       │
                       ▼
                      K3s
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
    ▼                  ▼                  ▼
    PostgreSQL        MinIO             Airflow
    Data Store      Object Store       Orchestrator
    │                  │                  │
    │                  │          ┌───────┴───────┐
    │                  │          ▼               ▼
    │                  │       FastAPI        Dashboard
    │                  │
    └──────────────────┴──────────────────────────┐
                                                   │
                                                   ▼
                                       W1-W10 Pipeline
                                       Orchestrated by
                                           Airflow
```

### AWS S3 in the Production Data Flow

The cloud deployment uses AWS S3 as the cloud-backed artifact layer between the Airflow-orchestrated data/ML pipeline and the application services.

```
                Oracle Cloud / K3s
                       │
                       ▼
                  Apache Airflow
                       │
                W1-W10 Pipeline
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
    PostgreSQL                  AWS S3
    structured data            cloud artifacts
                                     │
                                     ├── W7 features
                                     ├── W8 model
                                     ├── scaler
                                     ├── metrics
                                     └── W9 predictions
                                     │
                                     ▼
                          FastAPI / Dashboard
```

This creates a clear separation of responsibilities:

- **PostgreSQL** — structured relational data storage.
- **MinIO** — Kubernetes-hosted S3-compatible object storage used as part of the platform infrastructure.
- **AWS S3** — cloud-backed storage for the current data/ML/application artifacts used by the deployed workflow.
- **Apache Airflow** — orchestration layer responsible for coordinating processing and artifact publication.
- **FastAPI / Dashboard** — application layer consuming the current artifacts from S3.

The AWS S3 integration is also retained as the storage foundation for the planned P2-W6 model artifact tracking and lifecycle-management work.

### Infrastructure vs Orchestration

The production architecture has two related but different responsibilities:

**Kubernetes / K3s**

- Runs PostgreSQL
- Runs MinIO
- Runs Airflow
- Runs FastAPI
- Runs Dashboard
- Manages Pods, Services, Deployments and StatefulSets
- Provides persistent volumes for PostgreSQL and MinIO

**Apache Airflow**

- Orchestrates the W1-W10 data and ML workflow
- Coordinates pipeline tasks
- Coordinates processing dependencies and execution order
- Uses PostgreSQL and MinIO as platform services
- Coordinates outputs that are eventually consumed by FastAPI and the Dashboard

**GitHub Actions**

- Validates changes
- Runs tests
- Builds the unified Docker image
- Publishes the image to GHCR
- Deploys updated workloads to Oracle K3s

---

# Project Modules

| Stage | Module | Description | Main Technology |
|---|---|---|---|
| W1 | Data Collection & Cleaning | Collect and clean historical weather data | Python / Pandas |
| W2 | ETL Pipeline | Transform and prepare weather data for downstream processing | Python / Pandas |
| W3 | PostgreSQL Loader | Load structured weather data into PostgreSQL | PostgreSQL / Python |
| W4 | Airflow Orchestration | Orchestrate the complete W1-W10 pipeline | Apache Airflow |
| W5 | Spark ETL | Process weather data using distributed processing | PySpark |
| W6 | Data Lake + Dashboard | Store data/artifacts and provide visualisation | MinIO / S3 / Plotly Dash |
| W7 | Feature Engineering | Transform weather data into ML-ready features | Pandas / PyArrow |
| W8 | Machine Learning Model | Train and evaluate the prediction model | Scikit-learn |
| W9 | Batch Prediction | Generate predictions from the trained model | Python / Joblib |
| W10 | FastAPI + Dashboard | Serve predictions and integrate the Dashboard | FastAPI / Plotly Dash |
| P2-W1 | Kubernetes Foundation | Migrate the platform to Kubernetes | Kubernetes / K3s |
| P2-W2 | Platform Consolidation | Consolidate W1-W10 into one deployable image | Docker / Kubernetes |
| P2-W3 | Cloud Deployment | Deploy the platform to Oracle Cloud K3s | Oracle Cloud / K3s |
| P2-W4 | CI/CD | Automate validation, image publishing and deployment | GitHub Actions / GHCR |

---

Airflow is the control plane for this data/artifact movement. The application layer retrieves the latest S3 artifacts after the pipeline refreshes the deployed services.

# W1-W10 Data Flow

```
W1
│
├── Historical weather data
│
▼
W2
│
├── Cleaned / transformed data
│
▼
W3
│
├── PostgreSQL
│
▼
W4
│
├── Airflow orchestration
│
▼
W5
│
├── PySpark processing
│
▼
W6
│
├── MinIO / S3-compatible storage
├── Dashboard data
│
▼
W7
│
├── Feature engineering
├── ML-ready feature dataset
│
▼
W8
│
├── Model training
├── Model evaluation
│
▼
W9
│
├── Batch predictions
│
▼
W10
│
├── FastAPI prediction service
└── Interactive Dashboard
```

---

# Machine Learning Pipeline

Feature engineering means transforming the processed weather data into useful input variables that can be consumed by the machine-learning model.

```
Weather Data
    │
    ▼
W7 — Feature Engineering
    │
    │ Transform weather data
    │ into ML-ready features
    ▼
Feature Dataset
    │
    ▼
W8 — Model Training
    │
    ▼
Trained ML Model
    │
    ▼
W9 — Batch Prediction
    │
    ▼
Prediction Results
    │
    ▼
W10 — FastAPI
    │
    ▼
Dashboard
```

The trained model and prediction artifacts are integrated into the application layer so that predictions can be accessed through FastAPI and presented through the Dashboard.

---

# Technology Stack

## Data Engineering

- Python
- Pandas
- PostgreSQL
- PySpark
- Apache Airflow

## Storage

- PostgreSQL
- MinIO
- Amazon S3 (AWS S3)
- Kubernetes Persistent Volumes

### AWS S3 Cloud Data and Artifact Layer

AWS S3 is an active cloud object-storage layer in the deployed W1-W10 data and machine-learning workflow. It is used by the orchestration layer to persist processed datasets and ML/application artifacts.

The project uses:

```
AWS S3 Bucket: weather-data-lake-mlops
AWS Region: eu-west-2
```

The validated artifact flow is:

```
W1-W10 Pipeline
    │
    ▼
Apache Airflow
    │
    ▼
AWS S3
    ├── features/w7_features_final.parquet
    ├── models/best_model.pkl
    ├── models/scaler.pkl
    ├── models/model_metrics.json
    └── predictions/weather_predictions.csv
    │
    ▼
FastAPI / Dashboard
```

The orchestration package contains the cloud-storage integration used for S3 operations:

```
orchestration/
├── cloud_storage.py
└── test_cloud_storage.py
```

Airflow coordinates the W1-W10 processing lifecycle and uploads the resulting feature, model, prediction, and metrics artifacts to S3. The deployed FastAPI and Dashboard workloads then retrieve the current artifacts.

For Kubernetes deployment, the FastAPI and Dashboard workloads use AWS CLI-based init containers together with the `weather-env` Kubernetes Secret to download the required S3 artifacts before the application starts.

When a new pipeline execution produces updated artifacts, the Airflow lifecycle refreshes the application Pods. The replacement Pods download the latest S3 artifacts, preventing the application layer from serving stale predictions.

This establishes the deployed data/artifact lifecycle as:

```
Airflow
    ↓
W1-W10 Pipeline
    ↓
AWS S3
    ↓
Application Refresh
    ↓
FastAPI / Dashboard Pods replaced
    ↓
Latest S3 artifacts downloaded
    ↓
Updated prediction application
```

AWS S3 is therefore part of the production cloud architecture rather than a separate storage experiment.

## Machine Learning

- Scikit-learn
- Joblib
- PyArrow

## Application

- FastAPI
- Plotly Dash
- Uvicorn

## Infrastructure

- Docker
- Docker Compose
- Kubernetes
- K3s
- Oracle Cloud
- AWS S3
- Persistent Volumes / PVCs

## CI/CD

- GitHub
- GitHub Actions
- GitHub Container Registry (GHCR)
- Docker Buildx
- QEMU
- Multi-platform Docker images

---

# Phase 2 — Production Engineering

Phase 2 extends the original data engineering project into a cloud-native platform.

| Phase | Focus | Status |
|---|---|---|
| P2-W1 | Kubernetes Foundation + Airflow/W1-W9 Migration | Complete |
| P2-W2 | Platform Consolidation + W10 Integration | Complete |
| P2-W3 | Cloud / K3s Deployment | Complete |
| P2-W4 | CI/CD | In Progress |
| P2-W5 | Public Deployment | Planned |
| P2-W6 | MLflow + Platform Optimisation | Planned |
| P2-W7 | Comprehensive Testing | Planned |
| P2-W8 | Monitoring + Final Integration | Planned |

---

# P2-W1 — Kubernetes Foundation

The first Phase 2 stage established the Kubernetes foundation and migrated the existing platform components.

Key areas included:

- Kubernetes / K3s foundation
- Kubernetes node readiness
- PostgreSQL StatefulSet
- PostgreSQL PersistentVolumeClaim
- PostgreSQL Service
- MinIO StatefulSet
- MinIO PersistentVolumeClaim
- MinIO Service
- Airflow platform migration
- W1-W9 integration
- Kubernetes Secrets
- End-to-end platform validation

---

# P2-W2 — Platform Consolidation

The platform was consolidated around a single canonical project Dockerfile.

The unified image contains the dependencies and W1-W10 application code required by:

- Airflow
- W1-W9 processing
- Spark
- Machine learning
- FastAPI
- Dashboard

The same canonical image can therefore be used across the Docker and Kubernetes environments.

---

# P2-W3 — Oracle Cloud / K3s

The consolidated platform was deployed to an Oracle Cloud ARM64 VM running K3s.

Current Kubernetes workloads include:

```
PostgreSQL
MinIO
Airflow API Server
Airflow Scheduler
Airflow DAG Processor
Airflow Init Job
FastAPI Service
Dashboard Service
```
