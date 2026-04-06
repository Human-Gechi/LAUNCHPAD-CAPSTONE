from datetime import timedelta

import pendulum
from airflow.providers.smtp.notifications.smtp import SmtpNotifier
from airflow.sdk import dag, task, task_group
from airflow_dbt_python.operators.dbt import DbtRunOperator, DbtSnapshotOperator, DbtTestOperator

default_args = {
    "owner": "Human-Gechi",
    "email": "okoliogechi74@gmail.com",
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
}

DBT_PROJECT_DIR = "/opt/airflow/dbt_SupplyChain360"
DBT_PROFILE_NAME = "snowflake_credentials"

send_report = SmtpNotifier(
    from_email="okoliogechi74@gmail.com",
    to="okoliogechi74@gmail.com",
    subject="Supply Chain 360: {{ dag_run.state }}",
    html_content="""
    <h3>DAG Run Summary</h3>
    <p>DAG: {{ dag.dag_id }}</p>
    <p>Status: {{ dag_run.state }}</p>
    <p>View details in the UI: <a href="{{ ti.log_url }}">Logs</a></p>
    """,
)


@dag(
    dag_id="supply_chain_360",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 31),
    schedule="0 0 10 * *",
    catchup=False,
    on_success_callback=send_report,
    on_failure_callback=send_report,
)
def supplychain_360():
    @task(task_id="extract")
    def extract():
        from ingestion.main import main

        main()

    @task_group(group_id="snapshot")
    def snapshot():
        run = DbtSnapshotOperator(
            task_id="run",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:snapshot"],
            dbt_conn_id="snowflake_conn",
        )
        test = DbtTestOperator(
            task_id="test",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:snapshot"],
            dbt_conn_id="snowflake_conn",
        )
        run >> test

    @task_group(group_id="staging")
    def staging():
        run = DbtRunOperator(
            task_id="run",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:staging"],
            dbt_conn_id="snowflake_conn",
        )
        test = DbtTestOperator(
            task_id="test",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:staging"],
            dbt_conn_id="snowflake_conn",
        )
        run >> test

    @task_group(group_id="intermediate")
    def intermediate():
        run = DbtRunOperator(
            task_id="run",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:intermediate"],
            dbt_conn_id="snowflake_conn",
        )
        test = DbtTestOperator(
            task_id="test",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:intermediate"],
            dbt_conn_id="snowflake_conn",
        )
        run >> test

    @task_group(group_id="mart")
    def mart():
        run = DbtRunOperator(
            task_id="run",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:mart"],
            dbt_conn_id="snowflake_conn",
        )
        test = DbtTestOperator(
            task_id="test",
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            profile=DBT_PROFILE_NAME,
            select=["tag:mart"],
            dbt_conn_id="snowflake_conn",
        )
        run >> test

    extract_task = extract()
    staging_task = staging()
    intermediate_task = intermediate()
    mart_task = mart()
    snapshot_task = snapshot()

    extract_task >> snapshot_task >> staging_task >> intermediate_task >> mart_task


dag_instance = supplychain_360()
