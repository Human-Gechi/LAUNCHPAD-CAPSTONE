{{ config(
    materialized='view'
    )
}}

WITH products as (
    SELECT * FROM {{ ref('stg_products')}}
),

suppliers AS (
    SELECT * FROM {{ ref('stg_suppliers') }}
)

SELECT
    s.supplier_id,
    s.supplier_name,
    s.category AS supplier_category,
    s.country,
    p.product_id,
    p.product_name,
    p.brand,
    p.category AS product_category,
    p.unit_price
FROM products AS p
LEFT JOIN suppliers AS s
    ON p.supplier_id = s.supplier_id