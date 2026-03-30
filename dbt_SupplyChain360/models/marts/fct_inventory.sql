select
    warehouse_id,
    product_id,
    product_name,
    quantity_available,
    reorder_threshold,
    stock_status,
    stock_to_threshold_ratio
from {{ ref('int_inventory_health') }}