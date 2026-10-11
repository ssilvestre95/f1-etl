select
    constructor_id,
    name as constructor_name,
    nationality
from {{ source('f1', 'dim_constructor') }}