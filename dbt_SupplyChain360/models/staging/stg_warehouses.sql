select distinct
    cast(warehouse_id as varchar),               -- Unique identifier for warehouse
    cast(city as varchar),                       -- City where warehouse is located
    cast(state as varchar),                      -- State where warehouse is located
    cast(ingestion_date as date),             -- Timestamp when data was ingested
    cast(origin as varchar)                      -- Source system
from {{ source('supplychain360', 'warehouses') }}