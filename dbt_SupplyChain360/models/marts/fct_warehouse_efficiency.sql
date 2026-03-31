WITH base_data as (
   SELECT
        warehouse_id,
        warehouse_city,
        warehouse_state,
        shipment_id,
        transit_days,
        shipping_distance,
        route_performance_status,
        ingestion_date
    FROM {{ ref('int_warehouse_to_store_efficiency') }}
),

warehouse_aggregation AS (
    SELECT
        warehouse_id,
        warehouse_city,
        warehouse_state,
        count(DISTINCT shipment_id) AS total_shipments_processed,

        avg(transit_days) AS avg_transit_days,
        count(case when route_performance_status = 'Warehouse Delay' THEN 1 END) AS total_internal_delays,
        max(ingestion_date) AS last_updated_at
    FROM base_data
    GROUP BY 1, 2, 3
)

SELECT
    *,
    cast(total_internal_delays * 100.0 / nullif(total_shipments_processed, 0) as decimal(10,2)) as warehouse_error_rate_pct,
    CASE
        WHEN (total_internal_delays * 1.0 / nullif(total_shipments_processed, 0)) < 0.05 then 'High Efficiency'
        WHEN (total_internal_delays * 1.0 / nullif(total_shipments_processed, 0)) between 0.05 and 0.15 then 'Standard'
        ELSE 'Bottleneck Detected'
    END AS  efficiency_rating
FROM warehouse_aggregation