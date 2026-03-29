{{ config(
    materialized='incremental',
    unique_key = ['warehouse_id', 'product_id', 'snapshot_date']
    )
}}
select distinct
    coalesce(cast(warehouse_id as varchar), 'WH-XXX') as warehouse_id,           -- Unique identifier for warehouse
    coalesce(cast(product_id as varchar), 'PROD-XXXX') as product_id,            -- Unique identifier for product
    coalesce(abs(cast(quantity_available as number)), 0) as quantity_available,        -- Current stock level
    coalesce(abs(cast(reorder_threshold as number)), 0) as reorder_threshold,          -- Minimum stock before reorder
    coalesce(cast(snapshot_date as date), current_date) as snapshot_date,         -- Date of inventory snapshot
    cast(sheets_extraction_date as timestamp_ntz) as ingestion_date,                               -- Timestamp when data was ingested
    cast(origin as varchar) as origin,                                             -- Source system
    ingestion_date                                         -- Source system
from {{ source('supplychain360', 'inventory') }}

{% if is_incremental() %}
    WHERE ingestion_date >= (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}