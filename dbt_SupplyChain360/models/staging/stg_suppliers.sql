SELECT DISTINCT
    {{ clean_id('supplier_id', "'SUP-XXX'") }} as supplier_id,
    {{ clean_string('supplier_name') }} as supplier_name,
    {{ clean_string('category') }} as category,
    {{ clean_string('country') }} as country,
    cast(s3_extraction_date as timestamp_ntz) as s3_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'suppliers') }}