select
    user_id,
    account_id,
    email,
    role,
    created_at::timestamp as created_at
from {{ source('raw', 'raw_users') }}
