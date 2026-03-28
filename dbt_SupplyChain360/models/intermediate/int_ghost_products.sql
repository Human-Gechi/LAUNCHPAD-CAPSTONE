WITH max_transactions AS (
    SELECT MAX(transaction_timestamp_utc) AS snapshot_date
    FROM {{ ref('stg_transactions') }}
),

last_transaction_per_product AS (
    SELECT
        product_id,
        MAX(transaction_timestamp_utc) AS last_transaction_timestamp
    FROM {{ ref('stg_transactions') }}
    GROUP BY product_id
),

inventory_aging AS (
    SELECT
        i.product_id,
        DATEDIFF(
            'day',
            COALESCE(lt.last_transaction_timestamp, '2000-01-01'),
            mt.snapshot_date
        ) AS days_since_last_sale,
        i.quantity_available,
        CAST(i.quantity_available * p.unit_price AS DECIMAL(10,2)) AS capital_at_risk
    FROM {{ ref('stg_inventory') }} i
    LEFT JOIN {{ ref('stg_products') }} p ON i.product_id = p.product_id
    LEFT JOIN last_transaction_per_product lt ON i.product_id = lt.product_id
    CROSS JOIN max_transactions mt
)

SELECT *
FROM inventory_aging
ORDER BY days_since_last_sale DESC