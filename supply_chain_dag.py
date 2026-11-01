"""Airflow 2 DAG; requires apache-airflow-providers-databricks."""
from datetime import datetime, timezone
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

with DAG(
    "supply_chain_twin", start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule="@daily", catchup=False, max_active_runs=1,
    default_args={"retries": 2},
    doc_md="Run the configured Databricks job: ingest bronze, rebuild silver, publish gold.",
) as dag:
    rebuild = DatabricksRunNowOperator(
        task_id="reconstruct_shipments",
        databricks_conn_id="databricks_default",
        job_id="{{ var.value.twin_databricks_job_id }}",
    )
