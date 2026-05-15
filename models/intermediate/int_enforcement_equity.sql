{{
  config(
    materialized = 'view',
    tags = ['intermediate', 'equity', 'fairness']
  )
}}

-- Enforcement equity / disparate impact analysis.
--
-- Methodology: For each content category, compute the removal rate as a share
-- of total platform enforcement. Compare each category's rate to the platform
-- average using window functions. Categories where the removal rate exceeds
-- 1.5× the platform average are flagged for potential disparate impact review.
--
-- Why this belongs in T&S infrastructure: Over-enforcement in specific content
-- categories can suppress legitimate speech, chill expression in under-represented
-- communities, and create EU DSA Article 34 systemic risk liability. The 1.5×
-- threshold is a standard heuristic in algorithmic fairness literature (see:
-- EEOC 80% rule analogue applied to content enforcement).

with removals as (
    select * from {{ ref('stg_spotify_dsa_removals') }}
),

category_enforcement as (
    select
        enforcement_type,
        category,
        reporting_period,
        is_high_risk_category,
        sum(visibility_removal)             as category_removals,
        sum(account_termination)            as category_terminations,
        sum(account_suspension)             as category_suspensions,
        sum(total_enforcement_actions)      as category_total_actions,
        sum(num_measures_own_initiative)    as category_measures
    from removals
    group by 1, 2, 3, 4
),

platform_totals as (
    select
        enforcement_type,
        reporting_period,
        sum(category_removals)          as platform_total_removals,
        sum(category_total_actions)     as platform_total_actions,
        count(distinct category)        as num_categories
    from category_enforcement
    group by 1, 2
),

with_platform_avg as (
    select
        ce.*,
        pt.platform_total_removals,
        pt.platform_total_actions,
        pt.num_categories,
        -- platform average removal rate per category
        {{ safe_divide('pt.platform_total_removals', 'pt.num_categories') }}
            as platform_avg_removals_per_category,
        -- this category's share of total platform removals
        {{ safe_divide('ce.category_removals', 'pt.platform_total_removals') }}
            as category_removal_share,
        -- expected share if enforcement were uniform
        {{ safe_divide('1.0', 'pt.num_categories') }}
            as expected_uniform_share
    from category_enforcement ce
    left join platform_totals pt
        on ce.enforcement_type = pt.enforcement_type
        and ce.reporting_period = pt.reporting_period
),

with_window_metrics as (
    select
        *,
        -- removal rate relative to the per-category platform average
        {{ safe_divide('category_removals', 'platform_avg_removals_per_category') }}
            as removal_rate_vs_platform_avg,
        avg(category_removals) over (
            partition by enforcement_type, reporting_period
        )                               as window_avg_removals,
        stddev(category_removals) over (
            partition by enforcement_type, reporting_period
        )                               as window_stddev_removals,
        sum(category_removals) over (
            partition by enforcement_type, reporting_period
            order by category_removals desc
            rows between unbounded preceding and current row
        )                               as cumulative_removals_desc,
        rank() over (
            partition by enforcement_type, reporting_period
            order by category_removals desc
        )                               as removal_volume_rank
    from with_platform_avg
),

final as (
    select
        enforcement_type,
        category,
        reporting_period,
        is_high_risk_category,
        removal_volume_rank,
        category_removals,
        category_terminations,
        category_suspensions,
        category_total_actions,
        platform_total_removals,
        platform_avg_removals_per_category,
        category_removal_share,
        expected_uniform_share,
        removal_rate_vs_platform_avg,
        window_avg_removals,
        window_stddev_removals,
        cumulative_removals_desc,

        -- z-score: how many standard deviations above/below mean is this category?
        {{ safe_divide(
            'category_removals - window_avg_removals',
            'window_stddev_removals'
        ) }}                            as enforcement_z_score,

        -- deviation from expected uniform share (positive = over-enforced)
        category_removal_share - expected_uniform_share
                                        as share_deviation_from_uniform,

        -- 1.5× platform average disparate impact flag
        case
            when category_removals > 1.5 * platform_avg_removals_per_category
            then true
            else false
        end                             as disparate_impact_flag,

        -- severity tier for flagged categories
        case
            when category_removals > 3.0 * platform_avg_removals_per_category
            then 'critical'
            when category_removals > 2.0 * platform_avg_removals_per_category
            then 'high'
            when category_removals > 1.5 * platform_avg_removals_per_category
            then 'moderate'
            else 'within_norms'
        end                             as disparate_impact_severity,

        -- overturn rate proxy: null  -  not disclosed at category level in DSA report
        -- a production pipeline would join to internal case outcome data
        null::double                    as category_overturn_rate,

        case
            when category_removals > 1.5 * platform_avg_removals_per_category
            then 'Category flagged: removal rate exceeds 1.5× platform average. '
                 || 'Recommend policy team review for over-enforcement risk.'
            else 'Within normal enforcement distribution'
        end                             as equity_review_note

    from with_window_metrics
)

select * from final
