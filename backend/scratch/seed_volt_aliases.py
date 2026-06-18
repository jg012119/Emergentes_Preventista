import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin

def seed():
    db = get_supabase_admin()
    
    # 1. Get products
    products = db.table('products').select('*').execute().data
    if not products:
        print("No products found in DB")
        return
        
    prod_map = {p['name']: p['id'] for p in products}
    print("Available products:", list(prod_map.keys()))
    
    # Define seeds for Volt
    seeds = [
        ('Volt 300ml', 'volt chico', 'volt chico', 'size_alias', 0.95),
        ('Volt 300ml', 'voltcito', 'voltcito', 'cochabamba_slang', 0.95),
        ('Volt 300ml', 'cajita de volt', 'cajita de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'caja de volt', 'caja de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'cajas de volt', 'cajas de volt', 'unit_alias', 0.95),
        ('Volt 500ml', 'volt medio litro', 'volt medio litro', 'size_alias', 0.92),
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
            print(f"Failed to add alias '{alias_text}' -> '{prod_name}': {e}")
            
    print(f"Successfully seeded {inserted} Volt aliases in Supabase.")

if __name__ == '__main__':
    seed()
