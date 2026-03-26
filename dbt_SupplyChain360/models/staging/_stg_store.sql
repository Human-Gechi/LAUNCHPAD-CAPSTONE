select distinct
    store_id,                   -- Unique identifier for store
    store_name,                 -- Name of the store
    city,                       -- City where store is located
    state,                      -- State where store is located
    region,                     -- Regions
    store_open_date,            -- Date store opened
    ingestion_date,             -- Timestamp when data was ingested
    origin                      -- Source system
from {{ source('supplychain360', 'stores') }}