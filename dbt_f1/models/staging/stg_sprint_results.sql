select
    season,
    round,
    driver_id,
    constructor_id,
    grid,
    position,
    points,
    laps,
    status,
    race_time_ms,
    is_classified,
    (position = 1 and is_classified) as is_win,
    'sprint' as session_type
from {{ source('f1', 'fact_sprint_results') }}