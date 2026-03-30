SELECT DISTINCT
    product_id,
    product_name,
    brand,
    category,
    supplier_id,
    unit_price
FROM {{ ref('stg_products') }}
