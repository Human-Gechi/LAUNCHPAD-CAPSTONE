{{ config(
    materialized='incremental',
    unique_key = 'shipment_id'
    )
}}
select distinct
    coalesce(cast(shipment_id as varchar), 'UNKNOWN') as shipment_id,             -- Unique identifier for each shipment
    coalesce(cast(warehouse_id as varchar), 'WH-XXX') as warehouse_id,            -- Warehouse from which shipment originated
    coalesce(cast(store_id as varchar), 'STORE-XXXX') as store_id,                -- Store receiving the shipment
    coalesce(cast(product_id as varchar), 'PROD-XXXX') as product_id,             -- Product being shipped
    coalesce(abs(cast(quantity_shipped as number)), 0) as quantity_shipped,            -- Number of units shipped
    coalesce(cast(shipment_date as date), current_date) as shipment_date,         -- Date shipment was sent
    coalesce(cast(expected_delivery_date as date), current_date) as expected_delivery_date, -- Expected delivery date
    coalesce(cast(actual_delivery_date as date), current_date) as actual_delivery_date,     -- Actual delivery date
    coalesce(cast(carrier as varchar), 'UNKNOWN') as carrier,                     -- Shipping carrier
    cast(ingestion_date as timestamp) as ingestion_date,                               -- Timestamp when data was ingested
    cast(origin as varchar) as origin                                             -- Source system
from {{ source('supplychain360', 'shipments') }}

{% if is_incremental() %}
    WHERE ingestion_date >= (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}