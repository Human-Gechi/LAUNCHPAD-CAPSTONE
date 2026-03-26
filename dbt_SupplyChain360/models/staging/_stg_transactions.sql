select distinct
    "0" as transaction_id,      -- UUID (unique transaction identifier)
    "1" as store_id,            -- Unique identifier for stores
    "2" as product_id,          -- Unique identifier for products
    "3" as quantity,            -- Quantity bought
    "4" as unit_price,          -- Cost of each product
    "5" as discount,            -- Discount of products cost
    "6" as total_cost,          -- Total cost if discount is available
    "7" as transaction_ts,      -- Epoch/Unix time stored in microseconds
    ingested_at,                -- Time of ingestion
    source                      -- Data source
from {{ source('supplychain360', 'transactions') }}