with source as (
    select
        message_id,
        channel,
        sender,
        text,
        date,
        image_url,
        raw_data
    from raw.telegram_messages
)
select * from source; 