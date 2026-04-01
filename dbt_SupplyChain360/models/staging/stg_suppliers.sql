SELECT DISTINCT
    {{ clean_id('supplier_id', "'SUP-XXX'") }} AS supplier_id,
    {{ clean_string('supplier_name') }} AS supplier_name,
    {{ clean_string('category') }} AS category,
    {{ clean_string('country') }} AS country,
    cast(s3_extraction_date AS timestamp_ntz) AS s3_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'suppliers') }}
