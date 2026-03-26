select distinct
    cast(warehouse_id as varchar) as warehouse_id,           -- Unique identifier for warehouse
    cast(city as varchar) as city,                           -- City where warehouse is located
    cast(state as varchar) as state,                         -- State where warehouse is located
    cast(ingestion_date as date) as ingestion_date,          -- Timestamp when data was ingested
    cast(origin as varchar) as origin                        -- Source system
from {{ source('supplychain360', 'warehouses') }}