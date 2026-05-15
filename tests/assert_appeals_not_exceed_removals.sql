-- Custom test: total_complaints_submitted must never exceed total_moderation_actions.
-- DSA semantics: a user can only appeal a moderation decision that was made.
-- A violation here signals a data pipeline error or a broken join.

select
    reporting_period,
    total_complaints_submitted,
    total_moderation_actions
from {{ ref('stg_spotify_dsa_appeals') }}
where total_complaints_submitted > total_moderation_actions
