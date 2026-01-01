with channel_spend as (
    select
        ms.channel,
        sum(ms.spend) as total_spend,
        sum(ms.leads_generated) as total_leads
    from {{ ref('stg_marketing_spend') }} ms
    group by 1
),

channel_attribution as (
    select
        a.acquisition_channel,
        count(*) as accounts_acquired,
        sum(i.amount) as total_revenue
    from {{ ref('stg_accounts') }} a
    left join {{ ref('stg_invoices') }} i on a.account_id = i.account_id
    where i.status = 'Paid'
    group by 1
),

cac_calc as (
    select
        cs.channel,
        cs.total_spend,
        cs.total_leads,
        coalesce(ca.accounts_acquired, 0) as accounts_acquired,
        coalesce(ca.total_revenue, 0) as total_revenue,
        case
            when ca.accounts_acquired > 0 
            then round((cs.total_spend / ca.accounts_acquired)::numeric, 2)
            else null
        end as cac,
        case
            when ca.accounts_acquired > 0 
            then round((ca.total_revenue / ca.accounts_acquired)::numeric, 2)
            else null
        end as revenue_per_customer,
        case
            when cs.total_spend > 0 
            then round((ca.total_revenue / cs.total_spend)::numeric, 2)
            else null
        end as roas,
        case
            when ca.accounts_acquired > 0 and cs.total_spend > 0
            then round(((ca.total_revenue / ca.accounts_acquired) / (cs.total_spend / ca.accounts_acquired))::numeric, 1)
            else null
        end as ltv_cac_ratio
    from channel_spend cs
    left join channel_attribution ca on cs.channel = ca.acquisition_channel
)

select
    channel,
    total_spend,
    total_leads,
    accounts_acquired,
    total_revenue,
    cac,
    revenue_per_customer as rough_ltv,
    roas,
    ltv_cac_ratio,
    case
        when cac > 0 and revenue_per_customer > 0
        then round(((cac / (revenue_per_customer * 0.05)))::numeric, 1)
        else null
    end as cac_payback_months
from cac_calc
