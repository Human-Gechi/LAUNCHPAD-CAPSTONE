SELECT DISTINCT
    {{ clean_id('store_id', "'STORE-XXXX'") }} AS store_id,
    {{ clean_string('store_name') }} AS store_name,
    {{ clean_string('city') }} AS city,
    {{ clean_string('state') }} AS state,
    {{ clean_string('region') }} AS region,
    coalesce(
        to_date(store_open_date, 'DD/MM/YYYY'),
        to_date(store_open_date, 'MM/DD/YYYY'),
        to_date(store_open_date, 'YYYY-MM-DD'),
        current_date
    ) AS store_open_date,
    cast(sheets_extraction_date AS timestamp_ntz) AS sheets_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'stores') }}
