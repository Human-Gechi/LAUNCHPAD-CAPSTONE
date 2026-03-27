select distinct
    coalesce(cast("0" as varchar), 'UNKNOWN') as transaction_id,           -- Transaction ID
    coalesce(cast("1" as varchar), 'STORE-XXXX') as store_id,              -- Store ID
    coalesce(cast("2" as varchar), 'PROD-XXXX') as product_id,             -- Product ID
    coalesce(cast("3" as number), 0) as quantity,                          -- Quantity bought
    coalesce(cast("4" as float), 0.0) as unit_price,                       -- Unit price
    coalesce(cast("5" as float), 0.0) as discount,                         -- Discount
    coalesce(cast("6" as float), 0.0) as total_cost,                       -- Total cost
    to_timestamp_ntz(cast("7" as number) / 1000000) as transaction_timestamp_utc, -- Transaction timestamp (UTC)
    cast(ingestion_date as timestamp) as ingestion_date, -- Ingestion date
    cast(origin as varchar) as origin                  -- Data source
from {{ source('supplychain360', 'transactions') }}