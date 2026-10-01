{{
    config(
        materialized='incremental',
        unique_key='observation_id',
        incremental_strategy='append'
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['vehicle_id', 'trip_id', 'ingested_at']) }} as observation_id,
    route_id,
    vehicle_id,
    trip_id,
    block_id,
    direction,
    destination,
    minutes_late,
    is_late_known,
    lat,
    lon,
    heading,
    next_stop_id,
    next_stop_name,
    vehicle_timestamp,
    ingested_at
from {{ ref('int_vehicle_positions__deduped_typed') }}

{% if is_incremental() %}
where ingested_at > (select coalesce(max(ingested_at), '1900-01-01'::timestamp) from {{ this }})
{% endif %}
