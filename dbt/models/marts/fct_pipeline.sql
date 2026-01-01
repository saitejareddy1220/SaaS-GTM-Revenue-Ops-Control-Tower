with deal_metrics as (
    select
        d.segment,
        d.stage,
        count(*) as deal_count,
        avg(d.deal_value) as avg_deal_value,
        sum(d.deal_value) as total_deal_value,
        avg(d.sales_cycle_days) as avg_sales_cycle_days
    from {{ ref('stg_crm_deals') }} d
    group by 1, 2
),

win_rate as (
    select
        segment,
        count(*) filter (where stage = 'Closed Won') as won_deals,
        count(*) filter (where stage = 'Closed Lost') as lost_deals,
        count(*) as total_deals,
        round(
            count(*) filter (where stage = 'Closed Won')::numeric / 
            nullif(count(*), 0),
            3
        ) as win_rate
    from {{ ref('stg_crm_deals') }} d
    where stage in ('Closed Won', 'Closed Lost')
    group by 1
)

select
    dm.segment,
    dm.stage,
    dm.deal_count,
    dm.avg_deal_value,
    dm.total_deal_value,
    dm.avg_sales_cycle_days,
    wr.win_rate,
    wr.won_deals,
    wr.lost_deals
from deal_metrics dm
left join win_rate wr on dm.segment = wr.segment
