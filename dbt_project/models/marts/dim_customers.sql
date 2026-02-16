with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('int_orders_with_products') }}
),

customer_orders as (
    select
        customer_id,
        count(distinct order_id) as order_count,
        sum(order_amount) as total_amount,
        min(ordered_at) as first_order_at,
        max(ordered_at) as last_order_at
    from orders
    group by customer_id
),

final as (
    select
        customers.customer_id,
        customers.full_name,
        customers.email,
        customers.created_at,
        coalesce(customer_orders.order_count, 0) as order_count,
        coalesce(customer_orders.total_amount, 0) as total_amount,
        customer_orders.first_order_at,
        customer_orders.last_order_at
    from customers
    left join customer_orders on customers.customer_id = customer_orders.customer_id
)

select * from final
