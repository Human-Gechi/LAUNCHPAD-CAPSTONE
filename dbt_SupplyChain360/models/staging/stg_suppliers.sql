select distinct
    coalesce(cast(supplier_id as varchar), 'UNKNOWN') as supplier_id,            -- Unique supplier identifier
    coalesce(cast(supplier_name as varchar), 'UNKNOWN') as supplier_name,        -- Name of supplier
    coalesce(cast(category as varchar), 'UNKNOWN') as category,                  -- Category of products supplier deals in
    coalesce(cast(country as varchar), 'UNKNOWN') as country,                    -- Country supplier is based in
    coalesce(cast(ingestion_date as date), current_date) as ingestion_date,      -- Date the data was ingested from source s3 bucket to dest
    coalesce(cast(origin as varchar), 'UNKNOWN') as origin                       -- Data source
from {{ source('supplychain360', 'suppliers') }}