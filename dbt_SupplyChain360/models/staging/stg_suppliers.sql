select distinct
    cast(supplier_id as varchar) as supplier_id,             -- Unique identifier for supplier
    cast(supplier_name as varchar) as supplier_name,         -- Name of the supplier
    cast(category as varchar) as category,                   -- Category supplied
    cast(country as varchar) as country,                     -- Supplier country
    cast(ingestion_date as date) as ingestion_date,          -- Timestamp when data was ingested from source
    cast(origin as varchar) as origin                        -- Source system
from {{ source('supplychain360', 'suppliers') }}