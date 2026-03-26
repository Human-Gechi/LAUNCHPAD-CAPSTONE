select distinct
    cast(store_id as varchar),                   -- Unique identifier for store
    cast(store_name as varchar),                 -- Name of the store
    cast(city as varchar),                       -- City where store is located
    cast(state as varchar),                      -- State where store is located
    cast(region as varchar),                     -- Regions
    cast(store_open_date as date),            -- Date store opened
    cast(ingestion_date as date),             -- Timestamp when data was ingested
    cast(origin as varchar)                     -- Source system
from {{ source('supplychain360', 'stores') }}