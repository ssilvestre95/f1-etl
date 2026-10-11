with drivers as (
    select season, sum(points) as pts
    from {{ ref('driver_standings') }}
    group by season
),

teams as (
    select season, sum(weekend_points) as pts
    from {{ ref('constructor_points_by_race') }}
    group by season
)

select d.season, d.pts as driver_points, t.pts as constructor_points
from drivers d
join teams t on t.season = d.season
where d.pts <> t.pts