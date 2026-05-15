{{
  config(
    materialized = 'table',
    tags = ['mart', 'equity', 'compliance']
  )
}}

-- Equity audit mart  -  the above-and-beyond deliverable.
--
-- Purpose: Surface enforcement disparities across content categories for
-- legal and policy review. This model is the primary artifact for DSA Article 34
-- systemic risk assessments and internal fairness reviews.
--
-- Grain: one row per (enforcement_type, category).
--
-- Audience: T&S policy leads, legal counsel, external auditors.
--
-- Methodology note:
--   Enforcement rate = category's removal count / per-category platform average.
--   Disparate impact threshold = 1.5× (analogous to EEOC 4/5ths rule applied
--   to content enforcement rather than employment decisions).
--   Z-score identifies statistical outliers within the enforcement distribution.
--   This model intentionally exposes null overturn_rate: Spotify's public DSA
--   report does not disclose category-level appeal outcomes. A production version
--   would join to an internal case-management source to fill this gap.
--
-- Why fairness metrics belong in T&S infrastructure:
--   Content moderation decisions are not neutral. Automated systems trained on
--   historical data can encode existing biases  -  suppressing content from
--   under-represented communities at higher rates than the platform average.
--   Surfacing this in auditable dbt infrastructure creates an accountability layer
--   that is reproducible, testable, and explainable to regulators under the DSA.

with equity as (
    select * from {{ ref('int_enforcement_equity') }}
),

categories as (
    select
        category_code,
        category_description,
        category_label
    from {{ source('spotify_raw', 'categories') }}
    where category_code is not null
      and category_code != 'None'
),

final as (
    select
        e.enforcement_type,
        e.category                                      as category_code,
        coalesce(c.category_label, e.category)          as category_label,
        coalesce(c.category_description, e.category)    as category_description,
        e.reporting_period,
        e.is_high_risk_category,
        e.removal_volume_rank,

        -- enforcement volumes
        e.category_removals,
        e.category_terminations,
        e.category_suspensions,
        e.category_total_actions,
        e.platform_total_removals,

        -- equity metrics
        round(e.platform_avg_removals_per_category, 2)  as platform_avg_removals_per_category,
        round(e.category_removal_share, 6)              as category_removal_share,
        round(e.expected_uniform_share, 6)              as expected_uniform_share,
        round(e.share_deviation_from_uniform, 6)        as share_deviation_from_uniform,
        round(e.removal_rate_vs_platform_avg, 4)        as removal_rate_vs_platform_avg,
        round(e.enforcement_z_score, 4)                 as enforcement_z_score,

        -- disparate impact determination
        e.disparate_impact_flag,
        e.disparate_impact_severity,
        e.equity_review_note,

        -- overturn rate (null: not disclosed at category level in public DSA report)
        e.category_overturn_rate                        as overturn_rate,

        -- audit action recommendation
        case
            when e.disparate_impact_severity = 'critical'
            then 'URGENT: Policy review required. Category removal rate is >3× platform average.'
            when e.disparate_impact_severity = 'high'
            then 'HIGH PRIORITY: Schedule equity review within 30 days.'
            when e.disparate_impact_severity = 'moderate'
            then 'MONITOR: Flag for next quarterly review cycle.'
            when e.is_high_risk_category and not e.disparate_impact_flag
            then 'ROUTINE: High-risk category within normal enforcement bounds.'
            else 'OK: No disparate impact detected.'
        end                                             as audit_action,

        -- methodology footnote embedded for downstream report consumers
        'Disparate impact threshold: 1.5× platform average removals per category. '
        || 'Platform average computed as total_removals / num_active_categories '
        || 'within each enforcement_type. '
        || 'Source: Spotify DSA Transparency Report 2025, sheets 5 & 6. '
        || 'Overturn rates not available at category level in public disclosure.'
                                                        as methodology_note

    from equity e
    left join categories c on e.category = c.category_code
    order by
        e.enforcement_type,
        e.disparate_impact_flag desc,
        e.category_removals desc
)

select * from final
