with date_spine as (
    select
        date::date as date
    from generate_series(
        '2024-07-01'::date,
        '2025-12-31'::date,
        '1 day'::interval
    ) as date
)

select
    date,
    extract(year from date) as year,
    extract(month from date) as month,
    extract(quarter from date) as quarter,
    extract(day from date) as day,
    extract(dow from date) as day_of_week,
    to_char(date, 'Month') as month_name,
    to_char(date, 'Day') as day_name,
    extract(week from date) as week_of_year,
    date_trunc('month', date)::date as month_start_date,
    (date_trunc('month', date) + interval '1 month - 1 day')::date as month_end_date,
    date_trunc('quarter', date)::date as quarter_start_date,
    extract(doy from date) as day_of_year
from date_spine
