{% snapshot products_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='product_id',
      strategy='check',
      check_cols=['unit_price', 'category', 'brand', 'supplier_id', 'unit_price'],
      invalidate_hard_delete=True
    )
}}

SELECT
    product_id,
    product_name,
    category,
    brand,
    supplier_id,
    unit_price
FROM {{ ref('stg_products') }}
{% endsnapshot %}