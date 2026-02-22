select * from {{ source('public_raw', 'member_status_log') }}
