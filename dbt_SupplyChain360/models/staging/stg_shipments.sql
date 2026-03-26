select distinct
    shipment_id,                -- Unique identifier for each shipment
    warehouse_id,               -- Warehouse from which shipment originated
    store_id,                   -- Store receiving the shipment
    product_id,                 -- Product being shipped
    quantity_shipped,           -- Number of units shipped
    shipment_date,              -- Date shipment was sent
    expected_delivery_date,     -- Expected delivery date
    actual_delivery_date,       -- Actual delivery date
    carrier,                    -- Shipping carrier
    ingestion_date,             -- Timestamp when data was ingested
    origin                      -- Source system
from {{ source('supplychain360', 'shipments') }}