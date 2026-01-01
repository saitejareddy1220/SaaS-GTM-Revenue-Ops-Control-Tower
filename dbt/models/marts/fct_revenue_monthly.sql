with subscription_months as (
    -- Create a row for each subscription for each month it was active or should have been
    select
        s.account_id,
        s.subscription_id,
        d.date as revenue_month,
        s.end_date
    from {{ ref('stg_subscriptions') }} s
    cross join {{ ref('dim_date') }} d
    where d.date >= date_trunc('month', s.start_date)::date
      and d.date <= coalesce(date_trunc('month', s.end_date)::date, '2025-12-01'::date)
      and d.day = 1
),

monthly_revenue as (
    select
        sm.account_id,
        sm.revenue_month,
        coalesce(sum(i.amount), 0) as mrr,
        count(distinct i.invoice_id) as invoice_count,
        max(sm.end_date) as subscription_end_date
    from subscription_months sm
    left join {{ ref('stg_invoices') }} i 
        on sm.account_id = i.account_id
        and date_trunc('month', i.invoice_date)::date = sm.revenue_month
        and i.status = 'Paid'
    group by 1, 2
),

revenue_with_lag as (
    select
        account_id,
        revenue_month,
        mrr,
        subscription_end_date,
        lag(mrr) over (partition by account_id order by revenue_month) as prev_mrr,
        lead(mrr) over (partition by account_id order by revenue_month) as next_mrr
    from monthly_revenue
),

revenue_movements as (
    select
        account_id,
        revenue_month,
        mrr,
        prev_mrr,
        coalesce(prev_mrr, 0) as prev_mrr_clean,
        case
            when prev_mrr is null then mrr  -- new revenue
            when mrr > prev_mrr then mrr - prev_mrr  -- expansion
            when mrr < prev_mrr then prev_mrr - mrr  -- contraction
            else 0
        end as revenue_change,
        case
            when prev_mrr is null then 'new'
            when mrr > prev_mrr then 'expansion'
            when mrr < prev_mrr then 'contraction'
            when mrr = 0 and prev_mrr > 0 then 'churned'
            when next_mrr is null and subscription_end_date is not null then 'churned'
            else 'maintained'
        end as revenue_type
    from revenue_with_lag
)

select
    revenue_month,
    account_id,
    mrr,
    mrr * 12 as arr,
    prev_mrr_clean as prior_month_mrr,
    revenue_change,
    revenue_type,
    case when revenue_type = 'new' then mrr else 0 end as new_mrr,
    case when revenue_type = 'expansion' then revenue_change else 0 end as expansion_mrr,
    case when revenue_type = 'contraction' then revenue_change else 0 end as contraction_mrr,
    case when revenue_type = 'churned' then prev_mrr_clean else 0 end as churned_mrr,
    case
        when prev_mrr_clean > 0 
        then (mrr - prev_mrr_clean + case when revenue_type = 'expansion' then revenue_change else 0 end - case when revenue_type = 'contraction' then revenue_change else 0 end) / prev_mrr_clean
        else null
    end as nrr
from revenue_movements
where mrr > 0 or revenue_type = 'churned'  -- Include active revenue and churn events

