SELECT DISTINCT
    {{ clean_id('store_id', "'STORE-XXXX'") }} as store_id,
    {{ clean_string('store_name') }} as store_name,
    {{ clean_string('city') }} as city,
    {{ clean_string('state') }} as state,
    {{ clean_string('region') }} as region,
    coalesce(
        to_date(store_open_date, 'DD/MM/YYYY'),
        to_date(store_open_date, 'MM/DD/YYYY'),
        to_date(store_open_date, 'YYYY-MM-DD'),
        current_date
    ) as store_open_date,
    cast(sheets_extraction_date as timestamp_ntz) as sheets_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'stores') }}