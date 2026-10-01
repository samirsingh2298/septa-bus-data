-- Hard guard against the filter_sentinel_late() macro regressing: fails if
-- any row in the gold fact table still carries a 998/999 sentinel instead of
-- null.
select *
from {{ ref('fct_vehicle_observations') }}
where minutes_late in (998, 999)
