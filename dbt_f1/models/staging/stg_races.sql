select
    season,
    round,
    race_name,
    race_date,
    circuit_id,
    circuit_name,
    locality,
    country
from {{ source('f1', 'dim_race') }}