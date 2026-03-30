WITH shipments AS (
    SELECT
        shipment_date,
        actual_delivery_date,
        expected_delivery_date
    FROM
        {{ ref('stg_shipments') }}
)
SELECT *
FROM shipments
WHERE shipment_date >= actual_delivery_date
   OR shipment_date >= expected_delivery_date