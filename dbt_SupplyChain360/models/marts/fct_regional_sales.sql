WITH stores AS(
    SELECT * FROM {{ ref('stg_stores') }}
),

transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
)

SELECT
    st.region,
    SUM(t.quantity_sold) AS total_quantity_sold,
    SUM(t.net_revenue) AS total_revenue
FROM transactions AS t
INNER JOIN stores AS st ON t.store_id = st.store_id
GROUP BY st.region