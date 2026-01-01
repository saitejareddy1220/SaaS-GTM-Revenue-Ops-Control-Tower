select
    invoice_id,
    subscription_id,
    account_id,
    invoice_date::date as invoice_date,
    amount,
    status
from {{ source('raw', 'raw_invoices') }}
