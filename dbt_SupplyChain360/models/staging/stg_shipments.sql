{{ config(
    materialized='incremental',
    unique_key = 'shipment_id'
    )
}}
SELECT DISTINCT
    {{ clean_id('shipment_id', "'UNKNOWN'") }} AS shipment_id,
    {{ clean_id('warehouse_id', "'WH-XXX'") }} AS warehouse_id,
    {{ clean_id('store_id', "'STORE-XXXX'") }} AS store_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} AS product_id,
    {{ clean_number('quantity_shipped') }} AS quantity_shipped,
    coalesce(cast(shipment_date AS date), current_date) AS shipment_date,
    coalesce(cast(expected_delivery_date AS date), current_date)
        AS expected_delivery_date,
    coalesce(cast(actual_delivery_date AS date), current_date)
        AS actual_delivery_date,
    {{ clean_string('carrier') }} AS carrier,
    cast(s3_extraction_date AS timestamp_ntz) AS s3_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'shipments') }}

{% if is_incremental() %}
    WHERE ingestion_date > (SELECT max(ingestion_date) FROM {{ this }})
{% endif %}
