select distinct
    coalesce(cast(warehouse_id as varchar), 'WH-XXX') as warehouse_id,           -- Unique warehouse identifier
    coalesce(cast(city as varchar), 'UNKNOWN') as city,                          -- City where warehouse is located in the US
    coalesce(cast(state as varchar), 'UNKNOWN') as state,                        -- State where the warehouse is located in the US
    cast(ingestion_date as date) as ingestion_date,      -- Date the data was ingested from source s3 bucket to dest
    cast(origin as varchar) as origin                       -- Data source
from {{ source('supplychain360', 'warehouses') }}