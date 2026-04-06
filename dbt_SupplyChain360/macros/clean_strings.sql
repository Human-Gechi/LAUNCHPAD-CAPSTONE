{% macro clean_string(column_name, default_val="'UNKNOWN'") %}
    trim(coalesce(cast({{ column_name }} as varchar), {{ default_val }}))
{% endmacro %}