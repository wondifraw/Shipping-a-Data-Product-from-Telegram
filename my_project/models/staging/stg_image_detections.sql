with source as (
    select
        message_id,
        detected_object_class,
        confidence_score
    from raw.image_detections
)
select * from source; 