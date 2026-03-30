{{ config(
    materialized='incremental',
    unique_key = 'transaction_id'
    )
}}
SELECT DISTINCT
    {{ clean_id('transaction_id', "'UNKNOWN'") }} as transaction_id,
    {{ clean_id('store_id', "'STORE-XXXX'") }} as store_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} as product_id,
    {{ clean_number('quantity_sold') }} as quantity_sold,
    {{ clean_decimal('unit_price', 0.00) }} as unit_price,
    abs(cast(discount_pct as decimal(3,2))) as discount_pct,
    coalesce(
        cast(
            {{ clean_number('quantity_sold') }} *
            {{ clean_decimal('unit_price', 0.00) }} *
            (1 - abs(cast(discount_pct as decimal(3,2))))
        as decimal(10,2))
    , 0.00) as net_revenue,
    to_timestamp_tz(cast(transaction_timestamp as number) / 1000000) as transaction_timestamp_utc,
    cast(rds_extraction_date as timestamp_ntz) as rds_extraction_date,
    trim(cast(origin as varchar)) as origin,
    ingestion_date
FROM {{ source('supplychain360', 'transactions') }}
{% if is_incremental() %}
    WHERE ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}
