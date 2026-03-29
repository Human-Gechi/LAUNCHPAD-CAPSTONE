select distinct
    coalesce(cast(supplier_id as varchar), 'UNKNOWN') as supplier_id,            -- Unique supplier identifier
    coalesce(cast(supplier_name as varchar), 'UNKNOWN') as supplier_name,        -- Name of supplier
    coalesce(cast(category as varchar), 'UNKNOWN') as category,                  -- Category of products supplier deals in
    coalesce(cast(country as varchar), 'UNKNOWN') as country,                    -- Country supplier is based in
    cast(s3_extraction_date as timestamp_ntz) as ingestion_date,                               -- Timestamp when data was ingested
    cast(origin as varchar) as origin,  -- Data source                                           -- Source system
    ingestion_date
from {{ source('supplychain360', 'suppliers') }}