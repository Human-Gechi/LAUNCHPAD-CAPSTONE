SELECT DISTINCT
    warehouse_id,
    city,
    state
FROM {{ ref('stg_warehouses') }}