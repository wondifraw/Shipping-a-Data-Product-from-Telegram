select
    channel as channel_id,
    min(date) as first_message_date,
    max(date) as last_message_date
from {{ ref('stg_telegram_messages') }}
group by channel; 