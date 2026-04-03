{{ config(
    materialized='incremental',
    unique_key=['warehouse_id', 'product_id', 'snapshot_date', 'quantity_available', 'ingestion_date','reorder_threshold']
    )
}}
SELECT DISTINCT
    {{ clean_id('warehouse_id', "'WH-XXX'") }} AS warehouse_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} AS product_id,
    {{ clean_number('quantity_available') }} AS quantity_available,
    {{ clean_number('reorder_threshold') }} AS reorder_threshold,
    coalesce(cast(snapshot_date AS date), current_date) AS snapshot_date,
    cast(s3_extraction_date AS timestamp_ntz) AS s3_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'inventory') }}

{% if is_incremental() %}
    WHERE ingestion_date > (SELECT max(ingestion_date) FROM {{ this }})
{% endif %}
