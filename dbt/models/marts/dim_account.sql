select
    a.account_id,
    a.account_name,
    a.segment,
    a.company_size,
    a.region,
    a.acquisition_channel,
    a.created_at,
    a.status,
    s.plan_tier as current_plan_tier,
    s.start_date as subscription_start_date,
    case
        when s.status = 'Active' then 1
        else 0
    end as is_active_subscriber
from {{ ref('stg_accounts') }} a
left join {{ ref('stg_subscriptions') }} s
    on a.account_id = s.account_id
