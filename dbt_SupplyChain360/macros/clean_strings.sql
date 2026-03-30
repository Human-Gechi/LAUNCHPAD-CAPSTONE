{% macro clean_id(column_name, default_val="'UNKNOWN'") %}
    trim(coalesce(cast({{ column_name }} as varchar), {{ default_val }}))
{% endmacro %}