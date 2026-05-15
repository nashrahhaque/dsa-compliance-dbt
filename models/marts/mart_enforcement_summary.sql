{{
  config(
    materialized = 'table',
    tags = ['mart', 'enforcement']
  )
}}

-- Enforcement summary for T&S engineers and legal/policy teams.
-- Combines enforcement trends with appeal context.
-- Grain: one row per (enforcement_type, category).

with trends as (
    select * from {{ ref('int_enforcement_trends') }}
),

appeals as (
    select * from {{ ref('int_appeal_outcomes') }}
),

equity as (
    select
        enforcement_type,
        category,
        disparate_impact_flag,
        disparate_impact_severity,
        removal_rate_vs_platform_avg
    from {{ ref('int_enforcement_equity') }}
),

final as (
    select
        t.enforcement_type,
        t.category,
        t.reporting_period,
        t.is_high_risk_category,
        t.volume_rank,
        t.enforcement_tier,

        -- enforcement volumes
        t.total_measures,
        t.automated_measures,
        t.total_removals,
        t.total_account_terminations,
        t.total_actions,
        t.automation_rate,

        -- trend indicators
        t.trend_direction,
        t.pct_diff_from_prev_category,

        -- equity flags from int_enforcement_equity
        e.disparate_impact_flag,
        e.disparate_impact_severity,
        e.removal_rate_vs_platform_avg,

        -- appeals context (period-level, joined for completeness)
        a.total_complaints_submitted,
        a.appeal_rate,
        a.automation_accuracy,
        a.automation_precision,
        a.automation_recall,
        a.compliance_risk_flag,
        a.compliance_risk_description,

        -- combined risk signal for legal prioritization
        case
            when t.is_high_risk_category and e.disparate_impact_flag
            then 'high_risk_and_disparate_impact'
            when t.is_high_risk_category
            then 'high_risk_category'
            when e.disparate_impact_flag
            then 'disparate_impact_only'
            else 'standard'
        end as legal_review_priority

    from trends t
    left join equity e
        on t.enforcement_type = e.enforcement_type
        and t.category = e.category
    left join appeals a
        on t.reporting_period = a.reporting_period
)

select * from final
