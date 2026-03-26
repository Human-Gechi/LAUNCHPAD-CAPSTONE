select distinct
    cast(warehouse_id as varchar),            -- Unique identifier for warehouse
    cast(product_id as varchar)              -- Unique identifier for product
    cast(quantity_available as number)       -- Current stock level
    cast(reorder_threshold as number),      -- Minimum stock before reorder
    cast(snapshot_date as date),            -- Date of inventory snapshot
    cast(ingestion_date as date),           -- Timestamp when data was ingested
    cast(origin as varchar)                    -- Source system
from {{ source('supplychain360', 'inventory') }}