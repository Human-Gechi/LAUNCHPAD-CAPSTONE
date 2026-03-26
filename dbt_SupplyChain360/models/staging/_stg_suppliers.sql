select distinct
    supplier_id,                -- Unique identifier for supplier
    supplier_name,              -- Name of the supplier
    category,                   -- Category supplied
    country,                    -- Supplier country
    ingestion_date,             -- Timestamp when data was ingested from source
    origin                      -- Source system
from {{ source('supplychain360', 'suppliers') }}