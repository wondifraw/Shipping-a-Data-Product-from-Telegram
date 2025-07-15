select
    d.message_id,
    d.detected_object_class,
    d.confidence_score,
    m.channel,
    m.date as message_date
from {{ ref('stg_image_detections') }} d
left join {{ ref('stg_telegram_messages') }} m
    on d.message_id = m.message_id; 