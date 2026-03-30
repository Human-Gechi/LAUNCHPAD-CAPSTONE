{{ config(
    materialized='incremental',
    unique_key = ['warehouse_id', 'product_id', 'snapshot_date', 'quantity_available', 'ingestion_date','reorder_threshold','']
    )
}}
SELECT DISTINCT
    {{ clean_id('warehouse_id', "'WH-XXX'") }} as warehouse_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} as product_id,
    {{ clean_number('quantity_available') }} as quantity_available,
    {{ clean_number('reorder_threshold') }} as reorder_threshold,
    coalesce(cast(snapshot_date as date), current_date) as snapshot_date,
    cast(s3_extraction_date as timestamp_ntz) as s3_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'inventory') }}

{% if is_incremental() %}
    WHERE ingestion_date > (select max(ingestion_date) from {{ this }})
{% endif %}

