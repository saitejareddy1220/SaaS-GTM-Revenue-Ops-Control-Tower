with account_cohorts as (
    select
        account_id,
        date_trunc('month', created_at)::date as cohort_month
    from {{ ref('stg_accounts') }}
),

cohort_activity as (
    select
        ac.cohort_month,
        i.account_id,
        date_trunc('month', i.invoice_date)::date as activity_month,
        floor(extract(epoch from (date_trunc('month', i.invoice_date) - ac.cohort_month)) / (30 * 86400))::int as months_since_cohort,
        sum(i.amount) as revenue
    from account_cohorts ac
    join {{ ref('stg_invoices') }} i on ac.account_id = i.account_id
    where i.status = 'Paid'
    group by 1, 2, 3, 4
),

cohort_retention as (
    select
        cohort_month,
        months_since_cohort,
        count(distinct account_id) as active_accounts,
        sum(revenue) as cohort_revenue
    from cohort_activity
    group by 1, 2
),

cohort_sizes as (
    select
        cohort_month,
        count(*) as cohort_size
    from account_cohorts
    group by 1
)

select
    cr.cohort_month,
    cs.cohort_size,
    cr.months_since_cohort,
    cr.active_accounts,
    cr.cohort_revenue,
    round(cr.active_accounts::numeric / nullif(cs.cohort_size, 0), 3) as retention_rate,
    1 - round(cr.active_accounts::numeric / nullif(cs.cohort_size, 0), 3) as churn_rate
from cohort_retention cr
join cohort_sizes cs on cr.cohort_month = cs.cohort_month
order by cr.cohort_month, cr.months_since_cohort
