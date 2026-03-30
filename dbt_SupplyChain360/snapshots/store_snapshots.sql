{% snapshot stores_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='store_id',
      strategy='check',
      check_cols=['city', 'state', 'region', 'store_name', 'store_open_date'],
      invalidate_hard_delete=True
    )
}}

SELECT
    store_id,
    store_name,
    city,
    state,
    region,
    store_open_date
FROM {{ ref('stg_stores') }}

{% endsnapshot %}