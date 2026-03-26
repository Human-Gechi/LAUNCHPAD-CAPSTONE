select distinct
    cast("0" as varchar) as transaction_id,      -- UUID (unique transaction identifier)
    cast("1" as varchar) as store_id,            -- Unique identifier for stores
    cast("2" as varchar) as product_id,          -- Unique identifier for products
    cast("3" as number) as quantity,             -- Quantity bought
    cast("4" as float) as unit_price,            -- Cost of each product
    cast("5" as float) as discount,              -- Discount of products cost
    cast("6" as float) as total_cost,            -- Total cost if discount is available
    cast("7" as bigint) as transaction_ts,       -- Epoch/Unix time stored in microseconds
    cast(ingestion_date as date) as ingestion_date,                              -- Time of ingestion
    cast(origin as varchar) as origin                                      -- Data source
from {{ source('supplychain360', 'transactions') }}