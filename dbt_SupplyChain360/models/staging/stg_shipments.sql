select distinct
    shipment_id,                -- Unique identifier for each shipment
    cast(warehouse_id as varchar),               -- Warehouse from which shipment originated
    cast(store_id as varchar), -- Store receiving the shipment
    cast(product_id as varchar),              -- Product being shipped
    cast(quantity_shipped as number),           -- Number of units shipped
    cast(shipment_date as date),              -- Date shipment was sent
    cast(expected_delivery_date as date),     -- Expected delivery date
    cast(actual_delivery_date as date),       -- Actual delivery date
    cast(carrier as varchar),                    -- Shipping carrier
    cast(ingestion_date as date),           -- Timestamp when data was ingested
    cast(origin as varchar)                       -- Source system
from {{ source('supplychain360', 'shipments') }}