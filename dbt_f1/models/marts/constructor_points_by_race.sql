with weekend as (
    select
        season,
        round,
        constructor_id,
        sum(points) as weekend_points
    from {{ ref('fct_session_results') }}
    group by season, round, constructor_id
)

select
    w.season,
    w.round,
    r.race_name,
    r.race_date,
    w.constructor_id,
    c.constructor_name,
    w.weekend_points,
    sum(w.weekend_points) over (
        partition by w.season, w.constructor_id
        order by w.round
    ) as cumulative_points
from weekend w
join {{ ref('stg_races') }} r
    on r.season = w.season and r.round = w.round
join {{ ref('stg_constructors') }} c
    on c.constructor_id = w.constructor_id