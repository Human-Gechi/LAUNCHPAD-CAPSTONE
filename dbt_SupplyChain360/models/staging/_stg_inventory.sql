select distinct
    warehouse_id,               -- Unique identifier for warehouse
    product_id,                 -- Unique identifier for product
    quantity_available,         -- Current stock level
    reorder_threshold,          -- Minimum stock before reorder
    snapshot_date,              -- Date of inventory snapshot
    ingestion_date,             -- Timestamp when data was ingested
    origin                      -- Source system
from {{ source('supplychain360', 'inventory') }}