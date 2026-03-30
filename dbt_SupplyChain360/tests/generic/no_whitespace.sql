{% test no_whitespace(model, column_name) %}

SELECT *
FROM {{ model }}
WHERE {{ column_name }} != TRIM({{ column_name }})

{% endtest %}