FROM apache/airflow:3.1.5

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        vim \
        libpq-dev \
        gcc \
        libssl-dev \
        libffi-dev \
        default-libmysqlclient-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV AIRFLOW_UID=50000
USER airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --upgrade pip

COPY --chown=airflow:airflow logs /opt/airflow/logs
COPY --chown=airflow:airflow dags /opt/airflow/dags
COPY --chown=airflow:airflow config /opt/airflow/config
COPY --chown=airflow:airflow ingestion /opt/airflow/ingestion
COPY --chown=airflow:airflow dbt_SupplyChain360 /opt/airflow/dbt_SupplyChain360

WORKDIR /opt/airflow