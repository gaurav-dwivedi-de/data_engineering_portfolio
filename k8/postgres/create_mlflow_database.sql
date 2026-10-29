-- Create the MLflow database if it does not already exist.
-- Run with psql as a PostgreSQL role that can create databases.

SELECT 'CREATE DATABASE mlflow OWNER airflow'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'mlflow'
)
\gexec
