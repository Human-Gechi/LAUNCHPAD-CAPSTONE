SELECT DISTINCT
    {{ clean_id('warehouse_id', "'WH-XXX'") }} AS warehouse_id,
    {{ clean_string('city') }} AS city,
    {{ clean_string('state') }} AS state,
    cast(s3_extraction_date AS timestamp_ntz) AS s3_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'warehouses') }}
