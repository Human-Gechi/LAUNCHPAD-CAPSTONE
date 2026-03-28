{{ config(
    materialized='incremental',
    unique_key = 'transaction_id'
    )
}}
select distinct
    coalesce(cast("0" as varchar), 'UNKNOWN') as transaction_id,
    coalesce(cast("1" as varchar), 'STORE-XXXX') as store_id,
    coalesce(cast("2" as varchar), 'PROD-XXXX') as product_id,
    coalesce(abs(cast("3" as number(10,2))), 0) as quantity,
    coalesce(abs(cast("4" as decimal(10,2))), 0.00) as unit_price,
    abs(cast("5" as decimal(3,2))) as discount,
    coalesce(
        cast(
            coalesce(abs(cast("3" as number(10,2))), 0) *
            coalesce(abs(cast("4" as decimal(10,2))), 0.00) *
            (1 - abs(cast("5" as decimal(3,2))))
        as decimal(10,2))
    , 0.00) as net_revenue,
    to_timestamp_ntz(cast("7" as number) / 1000000) as transaction_timestamp_utc,
    cast(ingestion_date as timestamp) as ingestion_date,
    cast(origin as varchar) as origin
from {{ source('supplychain360', 'transactions') }}

{% if is_incremental() %}
    WHERE ingestion_date >= (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}