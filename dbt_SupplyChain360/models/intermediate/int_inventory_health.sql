{{ config(
    materialized='incremental',
    unique_key = ['warehouse_id', 'product_id']
    )
}}
WITH inventory as (
    SELECT * FROM {{ ref('stg_inventory') }}
),

products as (
    SELECT * FROM {{ ref('stg_products') }}
),

stock_levels AS (
    SELECT
        i.warehouse_id,
        p.product_id,
        p.product_name,
        i.quantity_available,
        i.reorder_threshold,
        CAST(i.quantity_available / i.reorder_threshold AS DECIMAL(10,2)) as stock_to_threshold_ratio,
        CASE
            WHEN i.quantity_available = 0 THEN 'Stock-Out'
            WHEN CAST(i.quantity_available / i.reorder_threshold AS DECIMAL(10,2)) < 1.0 THEN 'Below Reorder Threshold'
            WHEN CAST(i.quantity_available / i.reorder_threshold AS DECIMAL(10,2)) BETWEEN 1.0 AND 3.0 THEN 'Healthy'
            ELSE 'Sufficient'
        END AS stock_status,
        i.ingestion_date
    FROM
        inventory AS i
        JOIN products p ON i.product_id = p.product_id
)

SELECT * FROM stock_levels as stock
{% if is_incremental() %}
    WHERE stock.ingestion_date >= (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}
