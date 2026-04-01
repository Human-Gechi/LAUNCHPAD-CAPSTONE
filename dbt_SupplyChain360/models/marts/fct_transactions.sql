SELECT
    product_id,
    product_name,
    category,
    brand,
    store_id,
    supplier_id,
    SUM(quantity_sold) AS total_quantity_sold,
    SUM(gross_revenue) AS total_gross_revenue,
    SUM(total_expenses) AS total_expenses,
    SUM(net_revenue) AS total_net_revenue,
    SUM(net_profit_loss) AS total_net_profit_loss,
    AVG(profit_margin_pct) AS avg_profit_margin_pct,
    COUNT(DISTINCT transaction_id) AS num_transactions,
    MIN(ingestion_date) AS first_transaction_date,
    MAX(ingestion_date) AS last_transaction_date
FROM {{ ref('int_transactions_enriched') }}
GROUP BY 1, 2, 3, 4, 5
