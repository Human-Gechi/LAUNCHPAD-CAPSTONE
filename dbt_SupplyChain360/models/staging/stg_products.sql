select distinct
    coalesce(cast(product_id as varchar), 'PROD-XXXX') as product_id,            -- Unique products Identifier
    coalesce(cast(product_name as varchar), 'UNKNOWN') as product_name,          -- Name of products.
    coalesce(cast(category as varchar), 'UNKNOWN') as category,                  -- Product Categories
    coalesce(cast(brand as varchar), 'UNKNOWN') as brand,                        -- Product brand name
    coalesce(cast(supplier_id as varchar), 'UNKNOWN') as supplier_id,            -- Unique identifier for suppliers
    coalesce(cast(unit_price as float), 0.0) as unit_price,                      -- Cost of each product
    coalesce(cast(ingestion_date as date), current_date) as ingestion_date,      -- Date the data was ingested from source s3 bucket to dest
    coalesce(cast(origin as varchar), 'UNKNOWN') as origin                       -- Data source
from {{ source('supplychain360', 'products') }}