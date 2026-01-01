select
    ticket_id,
    account_id,
    category,
    severity,
    created_at::timestamp as created_at,
    resolved_at::timestamp as resolved_at,
    sla_hours,
    resolution_hours,
    sla_breached
from {{ source('raw', 'raw_support_tickets') }}
