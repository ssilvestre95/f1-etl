select season, round, driver_id, count(*) as n
from {{ ref('stg_race_results') }}
group by season, round, driver_id
having count(*) > 1