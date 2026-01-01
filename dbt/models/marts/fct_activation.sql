with user_activation as (
    select
        u.user_id,
        u.account_id,
        u.created_at as user_created_at,
        min(e.event_timestamp) filter (where e.event_type = 'activation') as activation_timestamp
    from {{ ref('stg_users') }} u
    left join {{ ref('stg_product_events') }} e
        on u.user_id = e.user_id
    group by 1, 2, 3
),

activation_metrics as (
    select
        account_id,
        count(*) as total_users,
        count(activation_timestamp) as activated_users,
        round(
            count(activation_timestamp)::numeric / nullif(count(*), 0),
            3
        ) as activation_rate,
        percentile_cont(0.5) within group (order by extract(epoch from (activation_timestamp - user_created_at)) / 86400) as median_days_to_activate
    from user_activation
    group by 1
)

select
    a.account_id,
    da.segment,
    da.acquisition_channel,
    a.total_users,
    a.activated_users,
    a.activation_rate,
    round(a.median_days_to_activate::numeric, 1) as median_days_to_activate
from activation_metrics a
join {{ ref('dim_account') }} da on a.account_id = da.account_id
