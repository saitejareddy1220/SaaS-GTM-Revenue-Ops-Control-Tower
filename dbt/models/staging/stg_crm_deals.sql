select
    deal_id,
    account_id,
    deal_value,
    stage,
    created_date::date as created_date,
    closed_date::date as closed_date,
    sales_cycle_days,
    segment
from {{ source('raw', 'raw_crm_deals') }}
