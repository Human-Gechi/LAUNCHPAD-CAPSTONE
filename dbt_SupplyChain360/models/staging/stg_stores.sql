select distinct
    coalesce(cast(store_id as varchar), 'STORE-XXXX') as store_id,                -- Unique identifier for store
    coalesce(cast(store_name as varchar), 'UNKNOWN') as store_name,               -- Name of the store
    coalesce(cast(city as varchar), 'UNKNOWN') as city,                           -- City where store is located
    coalesce(cast(state as varchar), 'UNKNOWN') as state,                         -- State where store is located
    coalesce(cast(region as varchar), 'UNKNOWN') as region,                       -- Regions
    coalesce(
        to_date(store_open_date, 'DD/MM/YYYY'),
        to_date(store_open_date, 'MM/DD/YYYY'),
        to_date(store_open_date, 'YYYY-MM-DD'),
        current_date
    ) as store_open_date,                                                         -- Date store opened
    cast(ingestion_date as timestamp) as ingestion_date,                               -- Timestamp when data was ingested
    cast(origin as varchar) as origin                                             -- Source system
from {{ source('supplychain360', 'stores') }}