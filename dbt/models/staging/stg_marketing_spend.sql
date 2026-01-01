select
    month::date as month,
    channel,
    spend,
    leads_generated,
    campaign_name
from {{ source('raw', 'raw_marketing_spend') }}
