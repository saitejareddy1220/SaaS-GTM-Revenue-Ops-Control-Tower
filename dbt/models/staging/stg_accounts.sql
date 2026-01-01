select
    account_id,
    account_name,
    segment,
    company_size,
    region,
    acquisition_channel,
    created_at::timestamp as created_at,
    status
from {{ source('raw', 'raw_accounts') }}
