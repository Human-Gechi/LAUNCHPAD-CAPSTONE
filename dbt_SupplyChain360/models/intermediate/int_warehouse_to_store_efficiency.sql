{{ config(
    materialized='incremental',
    unique_key = ['warehouse_id','store_id','shipment_id']
    )
}}

WITH shipments AS (
    SELECT * FROM {{ ref('stg_shipments') }}
),

stores AS (
    SELECT * FROM {{ ref('stg_stores') }}
),

warehouses AS (
    SELECT * FROM {{ ref('stg_warehouses') }}
),

base_locations AS (
    SELECT
        s.shipment_id,
        s.warehouse_id,
        s.store_id,
        st.city AS store_city,
        st.state AS store_state,
        w.city AS warehouse_city,
        w.state AS warehouse_state,
        s.ingestion_date,
        DATEDIFF('day', s.shipment_date, s.actual_delivery_date)
            AS transit_days,
        CASE
            WHEN st.city = w.city THEN 'Local (Same City)'
            WHEN st.state = w.state THEN 'Regional (Same State)'
            ELSE 'Long-Haul (Inter-State)'
        END AS shipping_distance
    FROM shipments AS s
    INNER JOIN stores AS st ON s.store_id = st.store_id
    INNER JOIN warehouses AS w ON s.warehouse_id = w.warehouse_id
)

SELECT
    *,
    CASE
        WHEN
            base.shipping_distance = 'Long-Haul (Inter-State)'
            AND base.transit_days > 3
            THEN 'High Delay Risk'
        WHEN
            base.shipping_distance = 'Local (Same City)'
            AND base.transit_days > 1
            THEN 'Warehouse Delay'
        ELSE 'Good Route'
    END AS route_performance_status
FROM base_locations AS base

{% if is_incremental() %}
    WHERE base.ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}
