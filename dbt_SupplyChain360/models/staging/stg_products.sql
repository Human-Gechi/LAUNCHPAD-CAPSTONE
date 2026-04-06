SELECT DISTINCT
    {{ clean_id('product_id', "'PROD-XXXX'") }} AS product_id,
    {{ clean_string('product_name') }} AS product_name,
    {{ clean_string('category') }} AS category,
    {{ clean_string('brand') }} AS brand,
    {{ clean_id('supplier_id', "'SUP-XXX'") }} AS supplier_id,
    {{ clean_decimal('unit_price', 0.00) }} AS unit_price,
    cast(s3_extraction_date AS timestamp_ntz) AS s3_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'products') }}
