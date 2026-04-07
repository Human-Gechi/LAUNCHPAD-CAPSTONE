{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}

    {# If a custom schema is provided, use it directly #}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
    {# Use schema provided in dbt_profile.yml #}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}
