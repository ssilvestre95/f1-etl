select season, round, sum(is_win::int) as winners
from {{ ref('stg_sprint_results') }}
group by season, round
having sum(is_win::int) <> 1
