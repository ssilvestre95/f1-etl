select * from {{ ref('stg_race_results') }}
union all
select * from {{ ref('stg_sprint_results') }}