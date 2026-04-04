{{ config(
    materialized='incremental',
    unique_key = ['shipment_id','warehouse_id']
    )
}}

WITH shipments AS (
    SELECT * FROM {{ ref('stg_shipments') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

stores AS (
    SELECT * FROM {{ ref('stg_stores') }}
),

shipments_tracking AS (
    SELECT
        s.shipment_id,
        s.warehouse_id,
        s.quantity_shipped,
        s.carrier,
        p.product_name,
        p.category,
        st.store_name,
        st.region,
        st.city,
        s.ingestion_date,
        DATEDIFF(DAY, s.expected_delivery_date, s.actual_delivery_date)
            AS delivery_delay_days,
        CASE
            WHEN s.actual_delivery_date < s.expected_delivery_date THEN 'Early'
            WHEN s.actual_delivery_date > s.expected_delivery_date THEN 'Late'
            ELSE 'On time'
        END AS delivery_status
    FROM shipments AS s
    INNER JOIN products AS p ON s.product_id = p.product_id
    INNER JOIN stores AS st ON s.store_id = st.store_id
)

SELECT * FROM shipments_tracking

{% if is_incremental() %}
    WHERE shipments_tracking.ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}