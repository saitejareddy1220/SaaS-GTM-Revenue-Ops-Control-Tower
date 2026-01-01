select
    event_id,
    user_id,
    account_id,
    event_type,
    event_timestamp::timestamp as event_timestamp
from {{ source('raw', 'raw_product_events') }}
