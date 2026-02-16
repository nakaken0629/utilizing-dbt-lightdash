with source as (
    select * from {{ ref('raw_orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        product_id,
        quantity,
        cast(ordered_at as date) as ordered_at
    from source
)

select * from renamed
