WITH transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

product_calculations AS (
    SELECT
        t.transaction_id,
        t.store_id,
        t.product_id,
        p.product_name,
        p.category,
        p.brand,
        p.supplier_id,
        t.quantity,
        t.unit_price AS selling_unit_price,
        p.unit_price AS supplier_unit_price,
        t.discount,
        t.net_revenue,
        cast((t.quantity * t.unit_price) as decimal(10,2)) AS gross_revenue,           
        cast((t.quantity * p.unit_price) as decimal(10,2)) AS total_expenses,
        cast(((t.quantity * t.unit_price) - t.net_revenue) as decimal(10,2)) AS discount_amount
    FROM transactions t
    LEFT JOIN products p ON t.product_id = p.product_id
)

SELECT
    pc.*,


    (pc.net_revenue - pc.total_expenses) AS net_profit_loss,
    CASE
        WHEN pc.net_revenue = 0 THEN 0
        ELSE cast(((pc.net_revenue - pc.total_expenses) / NULLIF(pc.gross_revenue, 0)) * 100 as decimal(10,2))
    END AS profit_margin_pct,

    CASE
        WHEN pc.net_revenue < pc.total_expenses THEN 'Loss'
        WHEN pc.net_revenue = pc.total_expenses THEN 'Breakeven'
        WHEN pc.net_revenue > pc.total_expenses AND pc.net_revenue < pc.gross_revenue THEN 'Profit (Discounted)'
        ELSE 'Full Profit'
    END AS financial_status

FROM product_calculations AS pc