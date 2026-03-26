select distinct
    cast(shipment_id as varchar) as shipment_id,                -- Unique identifier for each shipment
    cast(warehouse_id as varchar) as warehouse_id,              -- Warehouse from which shipment originated
    cast(store_id as varchar) as store_id,                      -- Store receiving the shipment
    cast(product_id as varchar) as product_id,                  -- Product being shipped
    cast(quantity_shipped as number) as quantity_shipped,       -- Number of units shipped
    cast(shipment_date as date) as shipment_date,               -- Date shipment was sent
    cast(expected_delivery_date as date) as expected_delivery_date, -- Expected delivery date
    cast(actual_delivery_date as date) as actual_delivery_date, -- Actual delivery date
    cast(carrier as varchar) as carrier,                        -- Shipping carrier
    cast(ingestion_date as date) as ingestion_date,             -- Timestamp when data was ingested
    cast(origin as varchar) as origin                           -- Source system
from {{ source('supplychain360', 'shipments') }}