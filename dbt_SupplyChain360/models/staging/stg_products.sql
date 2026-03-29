select distinct
    coalesce(cast(product_id as varchar), 'PROD-XXXX') as product_id,            -- Unique products Identifier
    coalesce(cast(product_name as varchar), 'UNKNOWN') as product_name,          -- Name of products.
    coalesce(cast(category as varchar), 'UNKNOWN') as category,                  -- Product Categories
    coalesce(cast(brand as varchar), 'UNKNOWN') as brand,                        -- Product brand name
    coalesce(cast(supplier_id as varchar), 'UNKNOWN') as supplier_id,            -- Unique identifier for suppliers
    coalesce(abs(cast(unit_price as decimal(10,2))), 0.00) as unit_price,        -- Cost of each product (decimal)
    cast(sheets_extraction_date as timestamp_ntz) as ingestion_date,                               -- Timestamp when data was ingested
    cast(origin as varchar) as origin,                                             -- Source system
    ingestion_date
from {{ source('supplychain360', 'products') }}