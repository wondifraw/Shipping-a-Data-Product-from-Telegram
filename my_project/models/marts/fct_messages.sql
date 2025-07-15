select
    m.message_id,
    c.channel_id,
    d.date_id,
    length(m.text) as message_length,
    case when m.image_url is not null then true else false end as has_image
from {{ ref('stg_telegram_messages') }} m
join {{ ref('dim_channels') }} c on m.channel = c.channel_id
join {{ ref('dim_dates') }} d on m.date = d.date_id; 