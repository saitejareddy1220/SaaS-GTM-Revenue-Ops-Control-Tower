with invalid_subscription_dates as (
    select
        subscription_id,
        account_id,
        start_date,
        end_date
    from {{ ref('stg_subscriptions') }}
    where end_date is not null
      and start_date > end_date
),

invalid_invoice_dates as (
    select
        i.invoice_id,
        i.account_id,
        i.invoice_date,
        s.start_date,
        s.end_date
    from {{ ref('stg_invoices') }} i
    join {{ ref('stg_subscriptions') }} s on i.subscription_id = s.subscription_id
    where i.invoice_date < s.start_date
       or (s.end_date is not null and i.invoice_date > s.end_date)
)

select * from invalid_subscription_dates
union all
select 
    null as subscription_id,
    account_id,
    invoice_date,
    start_date,
    end_date
from invalid_invoice_dates
