with orders_with_products as (
    select * from {{ ref('int_orders_with_products') }}
),

final as (
    select
        order_id,
        customer_id,
        product_id,
        product_name,
        category,
        quantity,
        price as unit_price,
        order_amount,
        ordered_at
    from orders_with_products
)

select * from final
