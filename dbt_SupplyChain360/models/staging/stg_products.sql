select distinct
    product_id,                 -- Unique identifier for product
    product_name,               -- Name of the product
    category,                   -- Product category
    brand,                      -- Product brand
    supplier_id,                -- Supplier of the product
    unit_price,                 -- Price per unit
    ingestion_date,             -- Timestamp when data was ingested
    origin                      -- Source system 
from {{ source('supplychain360', 'products') }}