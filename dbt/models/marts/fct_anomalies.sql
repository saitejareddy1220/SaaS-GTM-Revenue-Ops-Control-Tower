with monthly_metrics as (
    select
        revenue_month as metric_month,
        'MRR' as metric_name,
        sum(mrr) as metric_value
    from {{ ref('fct_revenue_monthly') }}
    group by 1
    
    union all
    
    select
        revenue_month as metric_month,
        'Churned MRR' as metric_name,
        sum(churned_mrr) as metric_value
    from {{ ref('fct_revenue_monthly') }}
    group by 1
    
    union all
    
    select
        revenue_month as metric_month,
        'New MRR' as metric_name,
        sum(new_mrr) as metric_value
    from {{ ref('fct_revenue_monthly') }}
    group by 1
),

metric_changes as (
    select
        metric_month,
        metric_name,
        metric_value,
        lag(metric_value) over (partition by metric_name order by metric_month) as prev_month_value,
        case
            when lag(metric_value) over (partition by metric_name order by metric_month) > 0
            then round(
                (((metric_value - lag(metric_value) over (partition by metric_name order by metric_month)) / 
                lag(metric_value) over (partition by metric_name order by metric_month)) * 100)::numeric,
                2
            )
            else null
        end as pct_change
    from monthly_metrics
)

select
    metric_month,
    metric_name,
    metric_value,
    prev_month_value,
    pct_change,
    case
        when abs(pct_change) > 20 then 'High Change'
        when abs(pct_change) > 10 then 'Moderate Change'
        else 'Normal'
    end as anomaly_severity,
    case
        when pct_change > 20 then 'Spike'
        when pct_change < -20 then 'Drop'
        else 'Normal'
    end as anomaly_type
from metric_changes
where abs(coalesce(pct_change, 0)) > 10
order by metric_month desc, abs(pct_change) desc
