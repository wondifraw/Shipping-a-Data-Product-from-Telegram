select *
from {{ ref('fct_messages') }}
where message_length = 0; 