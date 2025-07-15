with dates as (
    select distinct date as date
    from {{ ref('stg_telegram_messages') }}
)
select
    date as date_id,
    extract(year from date) as year,
    extract(month from date) as month,
    extract(day from date) as day,
    extract(dow from date) as day_of_week
from dates; 