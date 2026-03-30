{% snapshot suppliers_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='supplier_id',
      strategy='check',
      check_cols=['supplier_name', 'category', 'country'],
      invalidate_hard_delete=True
    )
}}

SELECT
    supplier_id,
    supplier_name,
    category,
    country
FROM {{ ref('stg_suppliers') }}

{% endsnapshot %}