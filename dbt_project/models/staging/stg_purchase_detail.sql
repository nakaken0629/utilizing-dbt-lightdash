select * from {{ source('public_raw', 'purchase_detail') }}
