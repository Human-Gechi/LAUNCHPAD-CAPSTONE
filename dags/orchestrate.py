from datetime import timedelta

import pendulum
from airflow.sdk import dag, task, task_group

default_args = {
    "owner": "Human-Gechi",
    "email": "okoliogechi74@gmail.com",
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
}

DBT_PROJECT_DIR = "/opt/airflow/dbt_SupplyChain360"
DBT_PROFILES_DIR = "/opt/airflow/dbt_SupplyChain360"


@dag(
    dag_id="supply_chain_360",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 31),
    schedule="0 0 10 * *",
    catchup=False,
)
def supplychain_360():
    @task(task_id="extract")
    def extract_task():
        from ingestion.main import main

        main()

    @task.bash(task_id="run_staging")
    def run_staging():
        return f"dbt run --select tag:staging --project-dir \
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="test_staging")
    def test_staging():
        return f"dbt test --select tag:staging --project-dir\
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="run_intermediate")
    def run_intermediate():
        return f"dbt run --select tag:intermediate --project-dir \
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="test_intermediate")
    def test_intermediate():
        return f"dbt test --select tag:intermediate --project-dir \
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="run_mart")
    def run_mart():
        return f"dbt run --select tag:mart --project-dir \
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="test_mart")
    def test_mart():
        return f"dbt test --select tag:mart --project-dir \
            {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="run_snapshot")
    def run_snapshot():
        return f"dbt snapshot --select tag:snapshot --project-dir\
              {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task.bash(task_id="test_snapshot")
    def test_snapshot():
        return f"dbt test --select tag:snapshot --project-dir \
              {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"

    @task_group(group_id="staging")
    def staging():
        s_run = run_staging()
        s_test = test_staging()
        s_run >> s_test

    @task_group(group_id="intermediate")
    def intermediate():
        i_run = run_intermediate()
        i_test = test_intermediate()
        i_run >> i_test

    @task_group(group_id="mart")
    def mart():
        m_run = run_mart()
        m_test = test_mart()
        m_run >> m_test

    @task_group(group_id="snapshot")
    def snapshot():
        snap_run = run_snapshot()
        snap_test = test_snapshot()
        snap_run >> snap_test

    extract = extract_task()
    staging_group = staging()
    intermediate_group = intermediate()
    mart_group = mart()
    snapshot_group = snapshot()

    extract >> staging_group >> intermediate_group >> mart_group >> snapshot_group


dag = supplychain_360()
