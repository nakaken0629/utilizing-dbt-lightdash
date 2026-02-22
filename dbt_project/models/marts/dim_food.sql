select
    f.id,
    f.name,
    f.category_id,
    c.name as category_name,
    f.price,
    f.created_at,
    f.updated_at
from {{ ref('stg_food') }} f
left join {{ ref('stg_category') }} c on f.category_id = c.id
