select
    driver_id,
    code as driver_code,
    given_name || ' ' || family_name as driver_name,
    date_of_birth,
    nationality
from {{ source('f1', 'dim_driver') }}