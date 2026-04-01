WITH stockout_products AS (
    SELECT * FROM {{ ref('int_inventory_health') }}
)

SELECT
    COUNT(*) AS stockout_events,
    product_id,
    product_name,
    warehouse_id
FROM stockout_products
WHERE stock_status = 'Stock_out'
GROUP BY 2, 3, 4
ORDER BY stockout_events DESC
LIMIT 10
