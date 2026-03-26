select distinct
    warehouse_id,               -- Unique identifier for warehouse
    city,                       -- City where warehouse is located
    state,                      -- State where warehouse is located
    ingestion_date,             -- Timestamp when data was ingested
    origin                      -- Source system
from {{ source('supplychain360', 'warehouses') }}