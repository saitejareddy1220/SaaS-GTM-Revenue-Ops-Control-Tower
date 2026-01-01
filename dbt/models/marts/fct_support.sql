with ticket_metrics as (
    select
        t.account_id,
        count(*) as total_tickets,
        count(*) filter (where t.severity = 'Critical') as critical_tickets,
        count(*) filter (where t.severity = 'High') as high_tickets,
        count(*) filter (where t.sla_breached = true) as sla_breached_tickets,
        round(
            count(*) filter (where t.sla_breached = true)::numeric / 
            nullif(count(*), 0),
            3
        ) as sla_breach_rate,
        avg(t.resolution_hours) as avg_resolution_hours,
        percentile_cont(0.5) within group (order by t.resolution_hours) as median_resolution_hours
    from {{ ref('stg_support_tickets') }} t
    group by 1
)

select
    tm.account_id,
    da.segment,
    da.region,
    tm.total_tickets,
    tm.critical_tickets,
    tm.high_tickets,
    tm.sla_breached_tickets,
    tm.sla_breach_rate,
    round(tm.avg_resolution_hours::numeric, 1) as avg_resolution_hours,
    round(tm.median_resolution_hours::numeric, 1) as median_resolution_hours,
    round((tm.total_tickets * 100.0)::numeric, 2) as tickets_per_100_accounts
from ticket_metrics tm
join {{ ref('dim_account') }} da on tm.account_id = da.account_id
