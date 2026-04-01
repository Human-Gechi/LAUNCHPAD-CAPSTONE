{% snapshot warehouses_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='warehouse_id',
      strategy='check',
      check_cols=['city', 'state'],
       invalidate_hard_delete=True
    )
}}


SELECT
    warehouse_id,
    city,
    state
FROM {{ ref('stg_warehouses') }}
{% endsnapshot %}