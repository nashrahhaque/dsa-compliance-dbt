{{
  config(
    materialized = 'view',
    tags = ['staging', 'enforcement']
  )
}}

with illegal_source as (
    select * from {{ source('spotify_raw', 'own_initiative_illegal') }}
),

tc_source as (
    select * from {{ source('spotify_raw', 'own_initiative_tc') }}
),

illegal_renamed as (
    select
        'illegal_content'                                       as enforcement_type,
        coalesce(category_of_illegal_content, 'UNKNOWN')        as category,
        sub_category_other,
        reporting_period,
        cast(num_measures_own_initiative as double)             as num_measures_own_initiative,
        cast(num_measures_automated as double)                  as num_measures_automated,
        cast(visibility_removal as double)                      as visibility_removal,
        cast(visibility_disable as double)                      as visibility_disable,
        cast(visibility_demoted as double)                      as visibility_demoted,
        cast(visibility_age_restricted as double)               as visibility_age_restricted,
        cast(visibility_interaction_restricted as double)       as visibility_interaction_restricted,
        cast(visibility_labelled as double)                     as visibility_labelled,
        cast(visibility_other as double)                        as visibility_other,
        cast(monetary_suspension as double)                     as monetary_suspension,
        cast(monetary_termination as double)                    as monetary_termination,
        cast(monetary_other as double)                          as monetary_other,
        cast(service_suspension as double)                      as service_suspension,
        cast(service_termination as double)                     as service_termination,
        cast(account_suspension as double)                      as account_suspension,
        cast(account_termination as double)                     as account_termination
    from illegal_source
    where category_of_illegal_content is not null
      and category_of_illegal_content != 'None'
      and category_of_illegal_content != 'TOTAL'
),

tc_renamed as (
    select
        'terms_and_conditions'                                  as enforcement_type,
        coalesce(category_tc, 'UNKNOWN')                        as category,
        sub_category_other,
        reporting_period,
        cast(num_measures_own_initiative as double)             as num_measures_own_initiative,
        cast(num_measures_automated as double)                  as num_measures_automated,
        cast(visibility_removal as double)                      as visibility_removal,
        cast(visibility_disable as double)                      as visibility_disable,
        cast(visibility_demoted as double)                      as visibility_demoted,
        cast(visibility_age_restricted as double)               as visibility_age_restricted,
        cast(visibility_interaction_restricted as double)       as visibility_interaction_restricted,
        cast(visibility_labelled as double)                     as visibility_labelled,
        cast(visibility_other as double)                        as visibility_other,
        cast(monetary_suspension as double)                     as monetary_suspension,
        cast(monetary_termination as double)                    as monetary_termination,
        cast(monetary_other as double)                          as monetary_other,
        cast(service_suspension as double)                      as service_suspension,
        cast(service_termination as double)                     as service_termination,
        cast(account_suspension as double)                      as account_suspension,
        cast(account_termination as double)                     as account_termination
    from tc_source
    where category_tc is not null
      and category_tc != 'None'
      and category_tc != 'TOTAL'
),

combined as (
    select * from illegal_renamed
    union all
    select * from tc_renamed
),

-- KEYWORD_OTHER appears once per parent category in the XLSX (reused sub-category code).
-- Aggregate to ensure one row per (enforcement_type, category).
aggregated as (
    select
        enforcement_type,
        category,
        reporting_period,
        min(sub_category_other)                     as sub_category_other,
        sum(coalesce(num_measures_own_initiative, 0))   as num_measures_own_initiative,
        sum(coalesce(num_measures_automated, 0))         as num_measures_automated,
        sum(coalesce(visibility_removal, 0))             as visibility_removal,
        sum(coalesce(visibility_disable, 0))             as visibility_disable,
        sum(coalesce(visibility_demoted, 0))             as visibility_demoted,
        sum(coalesce(visibility_age_restricted, 0))      as visibility_age_restricted,
        sum(coalesce(visibility_interaction_restricted, 0)) as visibility_interaction_restricted,
        sum(coalesce(visibility_labelled, 0))            as visibility_labelled,
        sum(coalesce(visibility_other, 0))               as visibility_other,
        sum(coalesce(monetary_suspension, 0))            as monetary_suspension,
        sum(coalesce(monetary_termination, 0))           as monetary_termination,
        sum(coalesce(monetary_other, 0))                 as monetary_other,
        sum(coalesce(service_suspension, 0))             as service_suspension,
        sum(coalesce(service_termination, 0))            as service_termination,
        sum(coalesce(account_suspension, 0))             as account_suspension,
        sum(coalesce(account_termination, 0))            as account_termination
    from combined
    group by 1, 2, 3
),

final as (
    select
        md5(enforcement_type || '|' || category) as removal_id,
        enforcement_type,
        category,
        sub_category_other,
        reporting_period,
        num_measures_own_initiative,
        num_measures_automated,
        visibility_removal,
        visibility_disable,
        visibility_demoted,
        visibility_age_restricted,
        visibility_interaction_restricted,
        visibility_labelled,
        visibility_other,
        monetary_suspension,
        monetary_termination,
        monetary_other,
        service_suspension,
        service_termination,
        account_suspension,
        account_termination,
        visibility_removal
            + visibility_disable
            + visibility_demoted
            + account_suspension
            + account_termination
            + service_suspension
            + service_termination
            + monetary_suspension
            + monetary_termination                           as total_enforcement_actions,
        {{ is_high_risk_category('category') }}              as is_high_risk_category
    from aggregated
)

select * from final
