{{
    config(
        materialized='incremental',
        unique_key=['route_id', 'observation_date'],
        incremental_strategy='delete+insert'
    )
}}

with fct as (
    select
        route_id,
        date_trunc('day', ingested_at) as observation_date,
        minutes_late,
        is_late_known
    from {{ ref('fct_vehicle_observations') }}

    {% if is_incremental() %}
    where ingested_at >= (select coalesce(max(observation_date), '1900-01-01'::timestamp) from {{ this }})
    {% endif %}
)

select
    route_id,
    observation_date,
    avg(minutes_late) filter (where is_late_known) as avg_minutes_late,
    count(*) as observation_count,
    count(*) filter (where is_late_known) as known_late_count,
    count(*) filter (where not is_late_known) as unknown_late_count
from fct
group by route_id, observation_date
