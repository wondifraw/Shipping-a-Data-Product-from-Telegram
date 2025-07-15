with source as (
    select
        (data->>'id')::bigint as message_id,
        data->>'channel' as channel,
        data->>'sender' as sender,
        data->>'text' as text,
        (data->>'date')::timestamp as date,
        data->>'image_url' as image_url
    from raw.telegram_messages
)
select * from source 