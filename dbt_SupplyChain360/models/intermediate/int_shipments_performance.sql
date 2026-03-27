with shipments as (
    select * from {{ ref('stg_shipments')}}
),
products as (
    select * from {{ ref('stg_products')}}
),
stores as (
    select * from {{ ref('stg_stores')}}
),

shipments_tracking as(
    select
        s.shipment_id,
        s.warehouse_id,
        s.quantity_shipped,
        s.carrier,
        p.product_name,
        p.category,
        st.store_name,
        st.region,
        st.city,
        datediff(day, s.expected_delivery_date, s.actual_delivery_date) as delivery_delay_days,
        case
        when s.actual_delivery_date < s.expected_delivery_date THEN 'Early'
        when s.actual_delivery_date > s.expected_delivery_date THEN 'Late'
        else 'On time'
    end as delivery_status
    from shipments as s
    inner join products as p on p.product_id = s.product_id
    inner join stores as st on st.store_id = s.store_id
)
select * from shipments_tracking