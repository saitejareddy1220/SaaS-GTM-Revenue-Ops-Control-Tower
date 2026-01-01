select
    invoice_id,
    account_id,
    invoice_date,
    amount
from {{ ref('stg_invoices') }}
where amount < 0

union all

select
    null as invoice_id,
    account_id,
    revenue_month as invoice_date,
    mrr as amount
from {{ ref('fct_revenue_monthly') }}
where mrr < 0
