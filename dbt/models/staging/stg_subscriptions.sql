select
    subscription_id,
    account_id,
    plan_tier,
    start_date::date as start_date,
    end_date::date as end_date,
    status
from {{ source('raw', 'raw_subscriptions') }}
