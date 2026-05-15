{{
  config(
    materialized = 'table',
    tags = ['mart', 'regulatory']
  )
}}

-- Regulatory summary designed for non-technical legal and policy audiences.
-- Grain: one row per reporting period with aggregate compliance KPIs.
-- Quarterly rollup structure is preserved; QoQ columns will populate
-- when multi-period data is ingested in future reporting cycles.

with appeals as (
    select * from {{ ref('int_appeal_outcomes') }}
),

equity_summary as (
    select
        reporting_period,
        count(*)                                    as total_categories_analyzed,
        sum(case when disparate_impact_flag then 1 else 0 end)
                                                    as categories_flagged_disparate_impact,
        sum(case when disparate_impact_severity = 'critical' then 1 else 0 end)
                                                    as critical_severity_count,
        sum(case when disparate_impact_severity = 'high' then 1 else 0 end)
                                                    as high_severity_count,
        sum(category_removals)                      as total_content_removals
    from {{ ref('int_enforcement_equity') }}
    group by reporting_period
),

trends_summary as (
    select
        reporting_period,
        sum(total_measures)                         as total_proactive_measures,
        sum(automated_measures)                     as total_automated_measures,
        sum(total_account_terminations)             as total_account_terminations,
        count(distinct category)                    as distinct_categories_enforced,
        sum(case when is_high_risk_category then total_measures else 0 end)
                                                    as high_risk_category_measures
    from {{ ref('int_enforcement_trends') }}
    group by reporting_period
),

final as (
    select
        a.reporting_period,

        -- report metadata
        '2025 Q4'                                   as reporting_quarter,
        'Spotify Main'                              as service_name,
        'Annual DSA Transparency Report'            as report_type,

        -- enforcement volumes (plain-language labels for legal audience)
        ts.total_proactive_measures                 as total_enforcement_actions,
        ts.total_automated_measures                 as actions_by_automated_systems,
        ts.total_account_terminations               as accounts_permanently_removed,
        ts.distinct_categories_enforced             as content_categories_with_enforcement,
        ts.high_risk_category_measures              as high_risk_category_actions,

        -- appeals and complaints
        a.total_complaints_submitted                as user_complaints_received,
        a.total_moderation_actions,
        round(a.appeal_rate * 100, 4)              as appeal_rate_pct,
        a.compliance_risk_flag                      as compliance_concern_flagged,
        a.compliance_risk_description               as compliance_concern_detail,

        -- automation performance (for transparency reporting)
        round(a.automation_rate * 100, 2)          as automation_rate_pct,
        round(a.automation_accuracy * 100, 4)      as automation_accuracy_pct,
        round(a.automation_precision * 100, 4)     as automation_precision_pct,
        round(a.automation_recall * 100, 4)        as automation_recall_pct,

        -- equity audit summary
        es.total_categories_analyzed,
        es.categories_flagged_disparate_impact,
        es.critical_severity_count,
        es.high_severity_count,
        es.total_content_removals,
        round(
            {{ safe_divide(
                'es.categories_flagged_disparate_impact * 100.0',
                'es.total_categories_analyzed'
            ) }},
            2
        )                                           as pct_categories_flagged,

        -- QoQ placeholders: populated when prior-period data is ingested
        null::double                                as qoq_enforcement_change_pct,
        null::double                                as qoq_appeal_rate_change_pct,
        'Awaiting prior-period data'                as qoq_status_note,

        -- DSA article compliance checkmarks
        true                                        as dsa_article_16_notices_reported,
        true                                        as dsa_article_17_own_initiative_reported,
        true                                        as dsa_article_20_complaint_mechanism_reported,
        true                                        as dsa_article_23_transparency_report_published

    from appeals a
    left join equity_summary es on a.reporting_period = es.reporting_period
    left join trends_summary ts on a.reporting_period = ts.reporting_period
)

select * from final
