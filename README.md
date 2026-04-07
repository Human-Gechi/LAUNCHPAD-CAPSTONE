# LAUNCHPAD-CAPSTONE PROJECT
### **PROJECT FOLDERS**
- [.github](.github/) → Github actions worflows
- [config](config/) → Contains Airflow config file
- [dags](dags/) → Dags folder for pipeline orchestration
- [dbt_SupplyChain360](dbt_SupplyChain360/) → dbt folder for data modelling
- [infrastructure](infrastructure/) → IAC for SupplyChain360
- [logs](logs/) → Contains log file configuration
- [tests](tests/) → Tests for .py files
- [.dockerignore](.dockerignore) → Files Docker ignores
- [.gitattributes](.gitattributes) → .py files formatting matching Linus EOF
- [.sqlfluff](.sqlfluff) → SQL linting file for dbt
- [.sqlfluffignore](.sqlfluffignore) → Folders/ files sqlfluff should ignore
- [ docker-compose.yml](docker-compose.yml) → Compose file for dags
- [Dockerfile](Dockerfile) → Dockerfile
- [pyproject.toml](pyproject.toml) → Ruff linting
- [pytest.ini](pytest.ini) → Pytest file config to match parent directory
- [requirements.txt](requirements.txt) → Project requirements

### **PROBLEM STATEMENT**
**SupplyChain360 currently suffers from severe operational inefficiencies due to data fragmentation. Critical supply chain data—including inventory snapshots, logistics logs, and sales transactions—is siloed across AWS S3, Google Sheets, and PostgreSQL. The lack of a centralized "source of truth" has resulted in frequent product stockouts, inefficient warehouse utilization, and delayed supplier deliveries.This project aims to solve these challenges by engineering a Unified Supply Chain Data Platform that automates the ingestion, cleaning, and modeling of cross-domain data to enable real-time, actionable insights for inventory optimization and supplier performance.**

### **SOLUTION ARICHECTURE**
![Architecture Diagram](_README/Architecture.svg)

**DATA SOURCES**
| Source        | Description                                                      |
| ------------- | ---------------------------------------------------------------- |
| S3 bucket     | Contains folders: inventory, products, warehouses, shipments, suppliers |
| Postgres DB   | Sales data                                                       |
| Google Sheets | Information about stores                                         |

To ensure modularity, maintainability, and efficient collaboration, the project is organized into dedicated branches, each focusing on a specific aspect of the workflow:

- ingest: Contains all Python code related to data ingestion, including scripts for interacting with AWS S3, Google Sheets, and PostgreSQL using the boto3 library and other connectors.

- infra: Manages Infrastructure as Code (IaC) for provisioning and configuring cloud resources required by the platform.

- modelling: Focuses on data modeling, transformation logic, and dbt project files for building analytics-ready datasets.

- dev: Serves as the main integration branch, where code from all feature branches is merged for linting, DAG definition, and end-to-end testing before deployment.
This branching strategy promotes separation of concerns, simplifies code reviews, and enables parallel development across different components of the project.


Ingestion Mechanism:
**S3 objects Extraction (s3_to_s3.py)**
Helper files
 `Utility.py`
- `get_aws_dst_params(conn_id="aws_dst")`:
Retrieves AWS credentials and bucket information from an Airflow connection.
- `time_stamp()` / `full_timestamp()`:
Utility functions for generating timestamps for metadata and unique file naming.
- `parquet_path(folder, filename):
Constructs a unique S3 key for Parquet files using the folder, filename, and timestamp.

`Write.py`
- `object_metadata(data_source, df)`:
Adds extraction date and origin metadata to a DataFrame(e.g sheets, rds, s3 as origin)
- `get_dest_s3_client(conn_id="aws_dst")`:
Returns a boto3 S3 client for the destination bucket using Airflow credentials.
- `write_parquet(df, data_source, folder, filename, conn_id="aws_dst")`:
Converts a DataFrame to Parquet format and uploads it to the destination S3 bucket.

S3 Buckets data extraction: Data extraction from this bucket utilised boto3 , airflow to securely store credentials at runtime.

- `S3ClientFactory`

  - `create_client(conn_id)`:
Static method to create a boto3 S3 client using credentials and region from an Airflow connection.

- MoveData
  - `__init__(src_client, dst_client, src_bucket, dst_bucket)`:
Initializes the class with source/destination S3 clients and bucket names.
  - `validate_folders(source)`:
Scans the source bucket for folders and file types under a given prefix.
  - `exists_by_basename(prefix, base)`:
Checks if a file with a given base name exists in the destination bucket.
  - `read_json_file(s3_key)`:
Reads a JSON file from S3 and returns a pandas DataFrame.
  - `read_csv_file(s3_key)`:
Reads a CSV file from S3 and returns a pandas DataFrame.
  - `process_csv_files(prefi)`:
Processes all CSV files under a given prefix in the source bucket.
  - `process_json_files(prefix)`:
Processes all JSON files under a given prefix in the source bucket.
  - `ingest_files(source)`:
Orchestrates the ingestion of files from the source to the destination bucket, converting them to Parquet format.

### **How tht functions work together**
S3ClientFactory creates S3 clients using credentials stored in Airflow.
MoveData validates, processes and checks for file existencein the source bucket, reading them as DataFrames.
 - If the object exists, no processing is done on the object i.e a skipping mechanism is applied

 - Files are converted to Parquet format with metadata using write_parquet and uploaded to the destination bucket.
  - Utility functions handle credential retrieval, timestamping, and S3 key generation.
  - On the event of a netwrok issue, the trial mechansims kickc in to preven the pipelin from failing abruptly

**Google Sheets Extraction (sheets.py)**
This module provides classes and methods for extracting data from Google Sheets and ingesting it into an S3 bucket, leveraging Airflow for credential management and logging.

Key Classes and Functions
- SheetsManager

Manages the connection to a Google Sheet using Airflow's GSheetsHook and the gspread library.
  - __init__(sheet_url=None, gcp_conn_id="gspred_credentials"):
Initializes the manager with the sheet URL and credentials. If no URL is provided, it uses the SHEETS_URL Airflow variable.
get_dataframe():
Fetches all values from the first worksheet and returns them as a pandas DataFrame.

- `SheetsParser`
Handles the ingestion of data from a Google Sheet into an S3 bucket.
  - _`_init__(dst_client, dst_bucket)`:
Initializes the parser with a destination S3 client and bucket.
  - `ingest_data(source, sheet_manager, df)`:
Uploads the provided DataFrame to S3 as a Parquet file, skipping the upload if the file already exists. Handles errors and logs the process.

#### **Workflow Overview**
`SheetsManager` connects to a Google Sheet and retrieves its data as a DataFrame.
`SheetsParser` checks if the data already exists in the destination S3 bucket.
The data is uploaded to S3 in Parquet format using the write_parquet utility.
All operations are logged for traceability and error handling.