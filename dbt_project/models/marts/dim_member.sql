select
    id,
    last_name,
    first_name,
    birth_date,
    gender,
    address,
    status,
    paid_at,
    quit_at,
    last_login_at,
    created_at,
    updated_at
from {{ ref('stg_member') }}
