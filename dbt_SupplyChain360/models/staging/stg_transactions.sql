{{ config(
    materialized='incremental',
    unique_key = 'transaction_id'
    )
}}
select distinct
    coalesce(cast(transaction_id as varchar), 'UNKNOWN') as transaction_id,
    coalesce(cast(store_id as varchar), 'STORE-XXXX') as store_id,
    coalesce(cast(product_id as varchar), 'PROD-XXXX') as product_id,
    coalesce(abs(cast(quantity_sold as number(10,2))), 0) as quantity_sold,
    coalesce(abs(cast(unit_price as decimal(10,2))), 0.00) as unit_price,
    abs(cast(discount_pct as decimal(3,2))) as discount_pct,
    coalesce(
        cast(
            coalesce(abs(cast(quantity_sold as number(10,2))), 0) *
            coalesce(abs(cast(unit_price as decimal(10,2))), 0.00) *
            (1 - abs(cast(discount_pct as decimal(3,2))))
        as decimal(10,2))
    , 0.00) as net_revenue,
    to_timestamp_ntz(cast(transaction_timestamp as number) / 1000000) as transaction_timestamp_utc,
    cast(rds_extraction_date as timestamp_ntz) as ingestion_date,
    cast(origin as varchar) as origin,
    ingestion_date
from {{ source('supplychain360', 'transactions') }}

{% if is_incremental() %}
    WHERE ingestion_date >= (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}