select distinct
    cast(product_id as varchar),                -- Unique identifier for product
    cast(product_name as varchar)            -- Name of the product
    cast(category as varchar),                   -- Product category
    cast(brand as varchar)                    -- Product brand
    cast(supplier_id as varchar),                -- Supplier of the product
    cast(unit_price as float),                 -- Price per unit
    cast(ingestion_date as date),             -- Timestamp when data was ingested
    cast(origin as varchar)                    -- Source system
from {{ source('supplychain360', 'products') }}