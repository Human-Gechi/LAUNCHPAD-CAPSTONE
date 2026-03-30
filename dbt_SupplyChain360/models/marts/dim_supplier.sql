SELECT DISTINCT
    supplier_id,
    supplier_name,
    category,
    country
FROM {{ ref('stg_suppliers') }}