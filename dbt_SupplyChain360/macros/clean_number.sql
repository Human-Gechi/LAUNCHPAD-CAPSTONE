{% macro clean_number(column_name, default_val=0) %}
    coalesce(abs(cast({{ column_name }} as number)), {{ default_val }})
{% endmacro %}