import asyncio
import json
from src.mercagasto.parsers.mercadona import MercadonaAPIClient

async def find_active_subcategories():
    client = MercadonaAPIClient()
    
    # Load categories.json to get subcategory IDs
    with open('src/mercagasto/storage/data/categorias.json', 'r') as f:
        data = json.load(f)
    
    # Extract subcategory IDs from the JSON structure
    subcategory_ids = []
    for main_category in data['results']:
        for subcategory in main_category['categories']:
            subcategory_ids.append({
                'id': subcategory['id'], 
                'name': subcategory['name'],
                'main_category': main_category['name']
            })
    
    print(f"Testing {len(subcategory_ids)} subcategories...")
    
    # Test first 10 subcategory IDs
    test_subcategories = subcategory_ids[:10]
    
    for subcategory in test_subcategories:
        try:
            products = await client.get_products_by_category(subcategory['id'])
            if products:
                print(f"✓ Subcategory {subcategory['id']} ({subcategory['name']}) works! Found {len(products)} products")
                # Show first product as example
                if products:
                    first_product = products[0]
                    print(f"  Example: {first_product.get('display_name', 'Unknown')} - {first_product.get('price', 'No price')}")
            else:
                print(f"✗ Subcategory {subcategory['id']} ({subcategory['name']}) returned no products")
        except Exception as e:
            print(f"✗ Subcategory {subcategory['id']} ({subcategory['name']}) failed: {e}")
    
    # Close the client session
    await client.close()

if __name__ == "__main__":
    asyncio.run(find_active_subcategories())