{{
  config(
    materialized = 'view',
    tags = ['intermediate', 'appeals']
  )
}}

-- Appeal outcomes and compliance risk assessment.
-- Combines Spotify's aggregate complaint data with automation performance metrics
-- to derive indicators that legal teams use to assess DSA Article 20 compliance.

with appeals as (
    select * from {{ ref('stg_spotify_dsa_appeals') }}
),

final as (
    select
        reporting_period,
        total_complaints_submitted,
        total_automated_actions,
        total_human_review_actions,
        total_moderation_actions,
        automation_accuracy,
        automation_precision,
        automation_recall,
        appeal_rate,
        automation_rate,

        -- false-positive proxy: 1 - precision
        -- represents the rate at which automated actions may incorrectly flag content
        round(1.0 - coalesce(automation_precision, 1), 6)  as false_positive_rate_proxy,

        -- false-negative proxy: 1 - recall
        -- represents violative content that automation misses
        round(1.0 - coalesce(automation_recall, 1), 6)     as false_negative_rate_proxy,

        -- complaints per 10k moderation actions (normalized dispute rate)
        round(
            {{ safe_divide('total_complaints_submitted * 10000.0', 'total_moderation_actions') }},
            2
        )                                                   as complaints_per_10k_actions,

        -- DSA Article 20 compliance flag:
        -- flag if appeal rate > 5% or human review < 10% of total actions
        case
            when {{ safe_divide(
                'total_complaints_submitted',
                'total_moderation_actions'
            ) }} > 0.05
            then true
            when {{ safe_divide(
                'total_human_review_actions',
                'total_moderation_actions'
            ) }} < 0.10
            then true
            else false
        end                                                 as compliance_risk_flag,

        case
            when {{ safe_divide(
                'total_complaints_submitted',
                'total_moderation_actions'
            ) }} > 0.05
            then 'High appeal rate  -  review complaint pathway'
            when {{ safe_divide(
                'total_human_review_actions',
                'total_moderation_actions'
            ) }} < 0.10
            then 'Low human review share  -  automation over-reliance'
            else 'Within compliance thresholds'
        end                                                 as compliance_risk_description,

        -- overturn_rate: null because Spotify does not disclose overturns in 2025 report
        -- a production system would source this from internal case management
        null::double                                        as overturn_rate

    from appeals
)

select * from final
