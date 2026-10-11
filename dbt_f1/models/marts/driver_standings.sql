with sessions as (
    select * from {{ ref('fct_session_results') }}
),

by_driver as (
    select
        season,
        driver_id,
        sum(points) as points,
        count(*) filter (where session_type = 'race' and is_win) as wins,
        count(*) filter (
            where session_type = 'race' and is_classified and position <= 3
        ) as podiums,
        count(*) filter (where session_type = 'race') as races
    from sessions
    group by season, driver_id
)

select
    b.season,
    rank() over (
        partition by b.season
        order by b.points desc, b.wins desc
    ) as championship_position,
    b.driver_id,
    d.driver_name,
    b.points,
    b.wins,
    b.podiums,
    b.races
from by_driver b
join {{ ref('stg_drivers') }} d on d.driver_id = b.driver_id