{{ config(
    materialized='incremental',
    unique_key = 'shipment_id'
    )
}}
SELECT DISTINCT
    {{ clean_id('shipment_id', "'UNKNOWN'") }} as shipment_id,
    {{ clean_id('warehouse_id', "'WH-XXX'") }} as warehouse_id,
    {{ clean_id('store_id', "'STORE-XXXX'") }} as store_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} as product_id,
    {{ clean_number('quantity_shipped') }} as quantity_shipped,
    coalesce(cast(shipment_date as date), current_date) as shipment_date,
    coalesce(cast(expected_delivery_date as date), current_date) as expected_delivery_date,
    coalesce(cast(actual_delivery_date as date), current_date) as actual_delivery_date,
    {{ clean_string('carrier') }} as carrier,
    cast(s3_extraction_date as timestamp_ntz) as s3_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'shipments') }}

{% if is_incremental() %}
    WHERE ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}