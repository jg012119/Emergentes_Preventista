import sys
sys.path.append('.')
from app.config import get_supabase_admin

def seed():
    db = get_supabase_admin()
    
    # 1. Get products
    products = db.table('products').select('*').execute().data
    if not products:
        print("No products found in DB")
        return
        
    prod_map = {p['name']: p['id'] for p in products}
    print("Available products:", prod_map.keys())
    
    # Define seeds
    seeds = [
        # Coca-Cola 500ml
        ('Coca-Cola 500ml', 'coca', 'coca', 'user_phrase', 0.90),
        ('Coca-Cola 500ml', 'coquita', 'coquita', 'user_phrase', 1.00),
        ('Coca-Cola 500ml', 'gaseosa negra', 'gaseosa negra', 'user_phrase', 0.90),
        ('Coca-Cola 500ml', 'refresco', 'refresco', 'user_phrase', 0.85),
        ('Coca-Cola 500ml', 'coca chica', 'coca chica', 'size_alias', 0.95),
        ('Coca-Cola 500ml', 'coca chiquita', 'coca chiquita', 'size_alias', 0.95),
        ('Coca-Cola 500ml', 'coca personal', 'coca personal', 'size_alias', 0.95),
        
        # Coca-Cola 1L
        ('Coca-Cola 1L', 'coca', 'coca', 'user_phrase', 0.90),
        ('Coca-Cola 1L', 'gaseosa negra', 'gaseosa negra', 'user_phrase', 0.90),
        ('Coca-Cola 1L', 'refresco', 'refresco', 'user_phrase', 0.85),
        ('Coca-Cola 1L', 'coca de litro', 'coca de litro', 'size_alias', 1.00),
        
        # Coca-Cola 2L
        ('Coca-Cola 2L', 'coca', 'coca', 'user_phrase', 0.90),
        ('Coca-Cola 2L', 'gaseosa negra', 'gaseosa negra', 'user_phrase', 0.90),
        ('Coca-Cola 2L', 'refresco', 'refresco', 'user_phrase', 0.85),
        ('Coca-Cola 2L', 'coca grande', 'coca grande', 'size_alias', 0.95),
        ('Coca-Cola 2L', 'coca familiar', 'coca familiar', 'size_alias', 0.95),
        
        # Agua Cielo 500ml
        ('Agua Cielo 500ml', 'agua', 'agua', 'user_phrase', 0.90),
        ('Agua Cielo 500ml', 'agüita', 'aguita', 'user_phrase', 1.00),
        ('Agua Cielo 500ml', 'agua sin gas', 'agua sin gas', 'user_phrase', 0.95),
        ('Agua Cielo 500ml', 'h2o', 'h2o', 'user_phrase', 0.90),
        ('Agua Cielo 500ml', 'hidratación', 'hidratacion', 'user_phrase', 0.85),
        
        # Agua Cielo 1L
        ('Agua Cielo 1L', 'agua', 'agua', 'user_phrase', 0.90),
        ('Agua Cielo 1L', 'agüita', 'aguita', 'user_phrase', 0.95),
        ('Agua Cielo 1L', 'agua sin gas', 'agua sin gas', 'user_phrase', 0.95),
        ('Agua Cielo 1L', 'h2o', 'h2o', 'user_phrase', 0.90),
        ('Agua Cielo 1L', 'hidratación', 'hidratacion', 'user_phrase', 0.85),
        
        # Agua Cielo 2.5L
        ('Agua Cielo 2.5L', 'agua', 'agua', 'user_phrase', 0.90),
        ('Agua Cielo 2.5L', 'agüita', 'aguita', 'user_phrase', 0.95),
        ('Agua Cielo 2.5L', 'agua sin gas', 'agua sin gas', 'user_phrase', 0.95),
        ('Agua Cielo 2.5L', 'h2o', 'h2o', 'user_phrase', 0.90),
        ('Agua Cielo 2.5L', 'hidratación', 'hidratacion', 'user_phrase', 0.85),
    ]
    
    inserted = 0
    for prod_name, alias_text, norm_alias, alias_type, weight in seeds:
        if prod_name not in prod_map:
            print(f"Skipping {prod_name} (not in product catalog)")
            continue
        pid = prod_map[prod_name]
        
        # Insert
        try:
            db.table('product_aliases').insert({
                'product_id': pid,
                'alias_text': alias_text,
                'normalized_alias': norm_alias,
                'alias_type': alias_type,
                'confidence_weight': weight,
                'is_active': True
            }).execute()
            print(f"Added alias '{alias_text}' -> '{prod_name}'")
            inserted += 1
        except Exception as e:
            # might already exist
            print(f"Failed to add alias '{alias_text}' -> '{prod_name}': {e}")
            
    print(f"Successfully seeded {inserted} aliases.")

if __name__ == '__main__':
    seed()
