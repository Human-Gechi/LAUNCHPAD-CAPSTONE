select distinct
    cast(store_id as varchar) as store_id,                   -- Unique identifier for store
    cast(store_name as varchar) as store_name,               -- Name of the store
    cast(city as varchar) as city,                           -- City where store is located
    cast(state as varchar) as state,                         -- State where store is located
    cast(region as varchar) as region,                       -- Regions
    coalesce(
        to_date(store_open_date, 'DD/MM/YYYY'),
        to_date(store_open_date, 'YYYY-MM-DD')
    ) as store_open_date   ,                                  -- Date store opened
    cast(ingestion_date as date) as ingestion_date,          -- Timestamp when data was ingested
    cast(origin as varchar) as origin                        -- Source system
from {{ source('supplychain360', 'stores') }}