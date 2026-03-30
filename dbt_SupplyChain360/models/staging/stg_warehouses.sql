SELECT DISTINCT
    {{ clean_id('warehouse_id', "'WH-XXX'") }} as warehouse_id,
    {{ clean_string('city') }} as city,
    {{ clean_string('state') }} as state,
    cast(s3_extraction_date as timestamp_ntz) as s3_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'warehouses') }}