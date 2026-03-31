import pendulum
from datetime import timedelta

from airflow.sdk import dag, task
from ingestion.main import main

default_args = {
    "owner": "Human-Gechi",
    "email": "okoliogechi74@gmail.com",
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
}

@dag(
    dag_id="supply_chain_360"
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 31),
    schedule="0 0 10 * *",
    catchup=False,
)
def supplychain_360():
    @task(task_id="extract")
    def extract_task():
        main()

    extract_task()

dag = supplychain_360()