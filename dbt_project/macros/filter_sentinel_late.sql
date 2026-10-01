{% macro filter_sentinel_late(column_name) %}
    case
        when {{ column_name }} in (998, 999) then null
        else {{ column_name }}
    end
{% endmacro %}
