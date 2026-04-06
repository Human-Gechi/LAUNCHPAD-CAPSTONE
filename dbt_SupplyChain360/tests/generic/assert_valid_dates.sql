{% test is_date_type(model, column_name) %}

with valid_date as (
    select
        {{ column_name }} as date_column
    from {{ model }}
),

validation_errors as (
    select
        date_column
    from valid_date
    where try_to_date(cast(date_column as varchar)) is null
      and date_column is not null
)

select * from validation_errors

{% endtest %}