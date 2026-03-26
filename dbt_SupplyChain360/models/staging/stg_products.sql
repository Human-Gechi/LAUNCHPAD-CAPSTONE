select distinct
    cast(product_id as varchar) as product_id,               -- Unique identifier for product
    cast(product_name as varchar) as product_name,           -- Name of the product
    cast(category as varchar) as category,                   -- Product category
    cast(brand as varchar) as brand,                         -- Product brand
    cast(supplier_id as varchar) as supplier_id,             -- Supplier of the product
    cast(unit_price as float) as unit_price,                 -- Price per unit
    cast(ingestion_date as date) as ingestion_date,          -- Timestamp when data was ingested
    cast(origin as varchar) as origin                        -- Source system
from {{ source('supplychain360', 'products') }}