SELECT DISTINCT
    {{ clean_id('product_id', "'PROD-XXXX'") }} as product_id,
    {{ clean_string('product_name') }} as product_name,
    {{ clean_string('category') }} as category,
    {{ clean_string('brand') }} as brand,
    {{ clean_id('supplier_id', "'SUP-XXX'") }} as supplier_id,
    {{ clean_decimal('unit_price', 0.00) }} as unit_price,
    cast(s3_extraction_date as timestamp_ntz) as s3_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'products') }}