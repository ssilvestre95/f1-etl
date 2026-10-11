select season, round, driver_id, count(*) as n
from {{ ref('stg_sprint_results') }}
group by season, round, driver_id
having count(*) > 1