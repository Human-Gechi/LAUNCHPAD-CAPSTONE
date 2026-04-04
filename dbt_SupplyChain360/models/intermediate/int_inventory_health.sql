{{ config(
    materialized='incremental',
    unique_key = ['warehouse_id', 'product_id',]
    )
}}
WITH inventory AS (
    SELECT * FROM {{ ref('stg_inventory') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

stock_levels AS (
    SELECT
        i.warehouse_id,
        p.product_id,
        p.product_name,
        i.quantity_available,
        i.reorder_threshold,
        i.ingestion_date,
        CAST(i.quantity_available / i.reorder_threshold AS DECIMAL(10, 2))
            AS stock_to_threshold_ratio,
        CASE
            WHEN i.quantity_available = 0 THEN 'Stock-Out'
            WHEN
                CAST(
                    i.quantity_available / i.reorder_threshold AS DECIMAL(10, 2)
                )
                < 1.0
                THEN 'Below Reorder Threshold'
            WHEN
                CAST(
                    i.quantity_available / i.reorder_threshold AS DECIMAL(10, 2)
                ) BETWEEN 1.0 AND 3.0
                THEN 'Healthy'
            ELSE 'Sufficient'
        END AS stock_status
    FROM
        inventory AS i
    INNER JOIN products AS p ON i.product_id = p.product_id
)

SELECT * FROM stock_level
{% if is_incremental() %}
    WHERE stock_level.ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}
