select distinct
    cast(warehouse_id as varchar) as warehouse_id,           -- Unique identifier for warehouse
    cast(product_id as varchar) as product_id,               -- Unique identifier for product
    cast(quantity_available as number) as quantity_available, -- Current stock level
    cast(reorder_threshold as number) as reorder_threshold,  -- Minimum stock before reorder
    cast(snapshot_date as date) as snapshot_date,            -- Date of inventory snapshot
    cast(ingestion_date as date) as ingestion_date,          -- Timestamp when data was ingested
    cast(origin as varchar) as origin                        -- Source system
from {{ source('supplychain360', 'inventory') }}