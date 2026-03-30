SELECT DISTINCT
    store_id,
    store_name,
    city,
    state,
    region
FROM {{ ref('stg_stores') }}