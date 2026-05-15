{{
  config(
    materialized = 'view',
    tags = ['intermediate', 'enforcement', 'trends']
  )
}}

-- Enforcement trend analysis by category.
-- Because the DSA report covers a single annual period, time-series LAG is not
-- available within this dataset. This model instead orders categories by
-- enforcement volume and uses LAG() to surface relative differences between
-- adjacent categories  -  a pattern ready to extend when multi-period data lands.

with removals as (
    select * from {{ ref('stg_spotify_dsa_removals') }}
),

category_totals as (
    select
        enforcement_type,
        category,
        reporting_period,
        is_high_risk_category,
        sum(num_measures_own_initiative)    as total_measures,
        sum(num_measures_automated)         as automated_measures,
        sum(visibility_removal)             as total_removals,
        sum(account_termination)            as total_account_terminations,
        sum(total_enforcement_actions)      as total_actions
    from removals
    group by 1, 2, 3, 4
),

with_automation_ratio as (
    select
        *,
        {{ safe_divide('automated_measures', 'total_measures') }} as automation_rate,
        row_number() over (
            partition by enforcement_type
            order by total_measures desc
        ) as volume_rank
    from category_totals
),

with_lag as (
    select
        *,
        -- period_over_period macro applied across ordered categories
        -- simulates the LAG pattern used in time-series contexts
        {{ period_over_period('total_measures', 'enforcement_type', 'volume_rank') }}
            as prev_category_measures,
        {{ period_over_period('total_removals', 'enforcement_type', 'volume_rank') }}
            as prev_category_removals
    from with_automation_ratio
),

final as (
    select
        enforcement_type,
        category,
        reporting_period,
        is_high_risk_category,
        volume_rank,
        total_measures,
        automated_measures,
        total_removals,
        total_account_terminations,
        total_actions,
        automation_rate,
        prev_category_measures,
        prev_category_removals,
        {{ safe_divide(
            'total_measures - prev_category_measures',
            'prev_category_measures'
        ) }} as pct_diff_from_prev_category,
        case
            when total_measures > coalesce(prev_category_measures, total_measures)
            then 'higher_than_prev'
            when total_measures < coalesce(prev_category_measures, total_measures)
            then 'lower_than_prev'
            else 'equal_or_baseline'
        end as trend_direction,
        case
            when volume_rank <= 5 then 'top_5'
            when volume_rank <= 10 then 'top_10'
            else 'long_tail'
        end as enforcement_tier
    from with_lag
)

select * from final
