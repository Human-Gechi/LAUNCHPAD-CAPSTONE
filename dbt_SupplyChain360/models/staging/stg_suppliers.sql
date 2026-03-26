select distinct
    cast(supplier_id as varchar),                -- Unique identifier for supplier
    cast(supplier_name as varchar),              -- Name of the supplier
    cast(category as varchar),                   -- Category supplied
    cast(country as varchar),                    -- Supplier country
    cast(ingestion_date as date),             -- Timestamp when data was ingested from source
    cast(origin as varchar)                     -- Source system
from {{ source('supplychain360', 'suppliers') }}