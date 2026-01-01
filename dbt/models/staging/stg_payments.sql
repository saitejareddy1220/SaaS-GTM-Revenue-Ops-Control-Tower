select
    payment_id,
    invoice_id,
    payment_date::date as payment_date,
    amount,
    payment_method
from {{ source('raw', 'raw_payments') }}
