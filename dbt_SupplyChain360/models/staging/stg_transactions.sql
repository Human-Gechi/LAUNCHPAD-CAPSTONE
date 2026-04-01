{{ config(
    materialized='incremental',
    unique_key = 'transaction_id'
    )
}}
SELECT DISTINCT
    {{ clean_id('transaction_id', "'UNKNOWN'") }} AS transaction_id,
    {{ clean_id('store_id', "'STORE-XXXX'") }} AS store_id,
    {{ clean_id('product_id', "'PROD-XXXX'") }} AS product_id,
    {{ clean_number('quantity_sold') }} AS quantity_sold,
    {{ clean_decimal('unit_price', 0.00) }} AS unit_price,
    abs(cast(discount_pct AS decimal(3, 2))) AS discount_pct,
    coalesce(
        cast(
            {{ clean_number('quantity_sold') }} *
            {{ clean_decimal('unit_price', 0.00) }} *
            (1 - abs(cast(discount_pct AS decimal(3, 2))))
            AS decimal(10, 2)
        ),
        0.00
    ) AS net_revenue,
    to_timestamp_tz(cast(transaction_timestamp AS number) / 1000000)
        AS transaction_timestamp_utc,
    cast(rds_extraction_date AS timestamp_ntz) AS rds_extraction_date,
    trim(cast(origin AS varchar)) AS origin,
    ingestion_date
FROM {{ source('supplychain360', 'transactions') }}
{% if is_incremental() %}
    WHERE ingestion_date > (SELECT max(ingestion_date) FROM {{ this }})
{% endif %}
