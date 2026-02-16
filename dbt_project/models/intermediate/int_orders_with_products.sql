with orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

joined as (
    select
        orders.order_id,
        orders.customer_id,
        orders.product_id,
        products.product_name,
        products.category,
        orders.quantity,
        products.price,
        orders.quantity * products.price as order_amount,
        orders.ordered_at
    from orders
    left join products on orders.product_id = products.product_id
)

select * from joined
