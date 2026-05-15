{% macro is_high_risk_category(col) %}
    case
        when {{ col }} ilike '%csam%'
            or {{ col }} ilike '%child%'
            or {{ col }} ilike '%terrorism%'
            or {{ col }} ilike '%violent_extremism%'
            or {{ col }} ilike '%STATEMENT_CATEGORY_VIOLENCE%'
            or {{ col }} ilike '%STATEMENT_CATEGORY_HATE%'
            or {{ col }} ilike '%STATEMENT_CATEGORY_ONLINE_CHILD%'
            or {{ col }} ilike '%STATEMENT_CATEGORY_CYBER%'
            or {{ col }} ilike '%STATEMENT_CATEGORY_NON_CONSENSUAL%'
        then true
        else false
    end
{% endmacro %}


{% macro safe_divide(numerator, denominator) %}
    case
        when ({{ denominator }}) = 0 or ({{ denominator }}) is null then null
        else ({{ numerator }})::double / ({{ denominator }})::double
    end
{% endmacro %}


{% macro period_over_period(metric_col, partition_col, order_col) %}
    lag({{ metric_col }}) over (
        partition by {{ partition_col }}
        order by {{ order_col }}
    )
{% endmacro %}
