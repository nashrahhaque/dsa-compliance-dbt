{{
  config(
    materialized = 'view',
    tags = ['staging', 'appeals']
  )
}}

-- Appeals data is very sparse in the DSA report: Spotify discloses only the
-- total complaint count (1,448). We enrich this with automated-means metrics
-- to build context around the appeals / moderation ratio.

with appeals_source as (
    select * from {{ source('spotify_raw', 'appeals') }}
),

automated_source as (
    select * from {{ source('spotify_raw', 'automated_means') }}
),

appeals_pivoted as (
    select
        reporting_period,
        max(case
            when indicator ilike '%complaints submitted%'
            then cast(value as double) end)         as total_complaints_submitted,
        max(case
            when indicator ilike '%complaints%' and indicator ilike '%ruled%'
            then cast(value as double) end)         as complaints_ruled_in_favour,
        max(case
            when indicator ilike '%reversed%'
            then cast(value as double) end)         as decisions_reversed
    from appeals_source
    group by reporting_period
),

automation_pivoted as (
    select
        reporting_period,
        max(case
            when indicator ilike '%solely%automated%'
            then cast(value as double) end)         as total_automated_actions,
        max(case
            when indicator ilike '%not taken%automated%'
            then cast(value as double) end)         as total_human_review_actions,
        max(case
            when indicator ilike '%accuracy%' and indicator not ilike '%precision%' and indicator not ilike '%recall%'
            then cast(value as double) end)         as automation_accuracy,
        max(case
            when indicator ilike '%precision%'
            then cast(value as double) end)         as automation_precision,
        max(case
            when indicator ilike '%recall%'
            then cast(value as double) end)         as automation_recall
    from automated_source
    group by reporting_period
),

final as (
    select
        a.reporting_period,
        coalesce(a.total_complaints_submitted, 0)   as total_complaints_submitted,
        a.complaints_ruled_in_favour,
        a.decisions_reversed,
        coalesce(am.total_automated_actions, 0)     as total_automated_actions,
        coalesce(am.total_human_review_actions, 0)  as total_human_review_actions,
        coalesce(am.total_automated_actions, 0)
            + coalesce(am.total_human_review_actions, 0) as total_moderation_actions,
        am.automation_accuracy,
        am.automation_precision,
        am.automation_recall,
        {{ safe_divide(
            'coalesce(a.total_complaints_submitted, 0)',
            'coalesce(am.total_automated_actions, 0) + coalesce(am.total_human_review_actions, 0)'
        ) }}                                        as appeal_rate,
        {{ safe_divide(
            'coalesce(am.total_automated_actions, 0)',
            'coalesce(am.total_automated_actions, 0) + coalesce(am.total_human_review_actions, 0)'
        ) }}                                        as automation_rate
    from appeals_pivoted a
    left join automation_pivoted am
        on a.reporting_period = am.reporting_period
)

select * from final
