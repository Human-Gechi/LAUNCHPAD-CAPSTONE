{% macro clean_decimal(column_name, default_val=0.0) %}
    coalesce(abs(cast({{ column_name }} as decimal(10,2))), {{ default_val }})
{% endmacro %}