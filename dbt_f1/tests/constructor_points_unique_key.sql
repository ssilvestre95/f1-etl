select season, round, constructor_id, count(*) as n
from {{ ref('constructor_points_by_race') }}
group by season, round, constructor_id
having count(*) > 1