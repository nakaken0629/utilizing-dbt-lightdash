select
    pd.id,
    pd.purchase_id,
    p.member_id,
    pd.food_id,
    p.purchased_at,
    p.shipping_address,
    pd.unit_price,
    pd.quantity,
    pd.subtotal
from {{ ref('stg_purchase_detail') }} pd
left join {{ ref('stg_purchase') }} p on pd.purchase_id = p.id
