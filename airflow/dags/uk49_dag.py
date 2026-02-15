"""UK49 ETL DAG

Runs nightly and executes the ETL tasks that scrape uk49s.net
and write draw results to the PostgreSQL database.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# import the ETL callable; ensure `airflow/scripts/etl_tasks.py` is available
import importlib.util
import os

# Load the local `etl_tasks.py` by path to avoid importing the installed
# `airflow` package (which would shadow this local package name).
etl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'etl_tasks.py'))
if not os.path.exists(etl_path):
    raise FileNotFoundError(f"etl_tasks.py not found at {etl_path}")
spec = importlib.util.spec_from_file_location('uk49_etl_tasks', etl_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
etl = getattr(mod, 'etl')

default_args = {
    'owner': 'uk49',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Run nightly at 02:00 UTC (change to your timezone if needed)
with DAG(
    dag_id='uk49_etl',
    default_args=default_args,
    schedule_interval='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    run_etl = PythonOperator(
        task_id='run_etl',
        python_callable=etl,
    )

    run_etl
