# 🌤️ Weather Intelligence Platform

> Production-grade end-to-end Data Engineering & MLOps platform for weather forecasting, pipeline orchestration, ML feature engineering, model training, and cloud deployment.

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)](https://github.com/gaurav-dwivedi-de/data_engineering_portfolio)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s-blue?style=for-the-badge&logo=kubernetes)](https://k3s.io)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=for-the-badge&logo=github)](https://github.com/features/actions)
[![Public API](https://img.shields.io/badge/Public-HTTPS%20Dashboard-green?style=for-the-badge)](https://ml.weather-intelligence.workers.dev/)

**Live Platform:** https://ml.weather-intelligence.workers.dev/

---

## Overview

This project is a complete data engineering and machine learning platform for processing weather data, orchestrating the full pipeline, generating ML-ready features, training prediction models, and serving forecasts through a production-style application stack.

The platform began as a 12-week data engineering and ML build and has since evolved into a cloud-native application using Docker, Kubernetes, Oracle Cloud, GitHub Actions, and GitHub Container Registry.

The system covers the complete lifecycle:

- Weather data collection and cleaning
- ETL processing
- PostgreSQL storage
- Apache Airflow orchestration
- PySpark processing
- MinIO / S3-compatible storage
- Feature engineering and transformation
- Machine learning model training and evaluation
- Batch prediction generation
- FastAPI prediction service
- Interactive weather prediction dashboard
- Docker containerization
- Kubernetes deployment
- Oracle Cloud K3s infrastructure
- GitHub Actions CI/CD
- GHCR image publishing
- Immutable commit-SHA container images
- Automated deployment to Oracle K3s
- Persistent storage for PostgreSQL and MinIO

---

## Architecture

### Data Engineering and ML Pipeline

Apache Airflow is the central orchestration layer for the W1-W10 pipeline. It coordinates the processing stages and the movement of data and artifacts between processing, storage, and application layers.

```text
                     WEATHER DATA
                           │
                           ▼
              ┌────────────────────────┐
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

### Airflow Role

Airflow acts as the central workflow orchestrator for the complete W1-W10 processing pipeline:

```text
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
├── Refreshes application workloads when new artifacts are published
└── Produces outputs consumed by FastAPI and the Dashboard
```

### Production / Cloud Architecture

```text
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
PostgreSQL           MinIO             Airflow
Data Store          Object Store      Orchestrator
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

The platform uses AWS S3 as the cloud-backed artifact layer between the Airflow-orchestrated pipeline and the application services.

```text
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

- **PostgreSQL** — structured relational data storage
- **MinIO** — Kubernetes-hosted S3-compatible object storage for platform infrastructure
- **AWS S3** — cloud-backed artifact storage for production models and predictions
- **Apache Airflow** — orchestration layer for pipeline execution and artifact publication
- **FastAPI / Dashboard** — application layer consuming the latest artifacts

---

## Project Modules

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
| P2-W5 | Public Deployment | Expose platform through public Cloudflare HTTPS route | Cloudflare / Traefik |
| P2-W6 | Infrastructure as Code | Manage Oracle infrastructure with Terraform | Terraform / OCI |

---

## W1-W10 Data Flow

```text
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

## Machine Learning Pipeline

```text
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

The trained model and prediction artifacts are integrated into the application layer so predictions can be accessed through FastAPI and shown in the Dashboard.

---

## Technology Stack

### Data Engineering

- Python
- Pandas
- PostgreSQL
- PySpark
- Apache Airflow

### Storage

- PostgreSQL
- MinIO
- Amazon S3 (AWS S3)
- Kubernetes Persistent Volumes

### Machine Learning

- Scikit-learn
- Joblib
- PyArrow

### Application

- FastAPI
- Plotly Dash
- Uvicorn

### Infrastructure

- Docker
- Docker Compose
- Kubernetes
- K3s
- Oracle Cloud
- AWS S3
- Persistent Volumes / PVCs

### CI/CD

- GitHub
- GitHub Actions
- GitHub Container Registry (GHCR)
- Docker Buildx
- QEMU
- Multi-platform Docker images

---

## Phase 2 — Production Engineering

Phase 2 extends the original project into a cloud-native platform.

| Phase | Focus | Status |
|---|---|---|
| P2-W1 | Kubernetes Foundation + Airflow/W1-W9 Migration | Complete |
| P2-W2 | Platform Consolidation + W10 Integration | Complete |
| P2-W3 | Cloud / K3s Deployment | Complete |
| P2-W4 | CI/CD | Complete |
| P2-W5 | Public Deployment | Complete |
| P2-W6 | Infrastructure as Code + Oracle Cloud Alignment | Complete |
| P2-W7 | Comprehensive Testing | Planned |
| P2-W8 | Monitoring + Final Integration | Planned |

### P2-W1 — Kubernetes Foundation

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

### P2-W2 — Platform Consolidation

The platform was consolidated around a single canonical Dockerfile and a unified application image.

The same image contains the dependencies and source required for:

- Airflow
- W1-W9 processing
- Spark
- Machine learning
- FastAPI
- Dashboard

### P2-W3 — Oracle Cloud / K3s

The platform was deployed to an Oracle Cloud ARM64 VM running K3s.

Current workloads include:

```text
PostgreSQL
MinIO
Airflow API Server
Airflow Scheduler
Airflow DAG Processor
Airflow Init Job
FastAPI Service
Dashboard Service
```

### P2-W4 — CI/CD Pipeline

The project includes an automated GitHub Actions workflow that validates the repository and builds a unified Docker image for multi-platform deployment.

Key capabilities include:

- Trigger on `push` and `pull_request` to `main`
- Repository structure validation
- Python 3.11 setup and compatibility checks
- Docker Buildx multi-platform builds
- GHCR image publication using git SHA tags
- Oracle K3s remote deployment via SSH
- Kubernetes rollout verification

### P2-W5 — Public Deployment

The platform is publicly accessible through Cloudflare and a K3s ingress layer.

Public endpoints:

```text
https://ml.weather-intelligence.workers.dev/         -> Dashboard
https://ml.weather-intelligence.workers.dev/api      -> FastAPI
https://ml.weather-intelligence.workers.dev/airflow/ -> Airflow
```

### P2-W6 — Infrastructure as Code

Terraform is used to describe the Oracle Cloud environment and align the deployment with the current OCI resources.

This includes:

- VCN creation and network definition
- Internet Gateway
- Route tables and security lists
- Oracle VM definition and inventory alignment
- State management with Terraform

---

## Quick start

### Local development

```bash
git clone https://github.com/gaurav-dwivedi-de/data_engineering_portfolio.git
cd data_engineering_portfolio
python -m venv .venv
source .venv/bin/activate
pip install -r docker_requirements.txt
```

### Docker Compose

```bash
docker-compose up -d
```

Then access:

- Airflow UI: http://localhost:8080
- FastAPI: http://localhost:8000/docs
- Dashboard: http://localhost:8051
- MinIO Console: http://localhost:9001

### Production deployment

```bash
git push origin main
```

This automatically triggers the GitHub Actions pipeline and deploys the latest image to Oracle K3s through GHCR.

---

## Project status and roadmap

### Completed

- W1-W10 complete pipeline
- Kubernetes deployment on Oracle Cloud
- Automated CI/CD pipeline
- Public dashboard access
- Terraform OCI infrastructure definition
- GHCR immutable image tagging

### Planned

- P2-W7: Comprehensive testing and validation
- P2-W8: Monitoring and final integration
- MLflow-based experiment tracking
- Advanced artifact lifecycle management

---

## Notes

This repository is designed as a portfolio-grade end-to-end data engineering and MLOps project showing operational maturity across data pipelines, cloud infrastructure, orchestration, machine learning, and deployment automation.

The platform is fully containerized, deployable to Kubernetes, and integrated with GitHub-based CI/CD workflows and public-facing dashboards.

---

## Repository links

- GitHub: https://github.com/gaurav-dwivedi-de/data_engineering_portfolio
- Live dashboard: https://ml.weather-intelligence.workers.dev/
- FastAPI: https://ml.weather-intelligence.workers.dev/api
- Airflow: https://ml.weather-intelligence.workers.dev/airflow/
