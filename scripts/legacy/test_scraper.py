#!/usr/bin/env python3
"""
Script de prueba para verificar el scraper de productos de Mercadona.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent if current_dir.name == 'src' else current_dir
sys.path.insert(0, str(root_dir))

from src.mercagasto.processors.mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from src.mercagasto.config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def test_single_subcategory():
    """Prueba con una sola subcategoría (Tónica y bitter - ID 161)."""
    print("🧪 Probando extracción de subcategoría 161 (Tónica y bitter)...")
    
    # Crear cliente API
    api_client = MercadonaAPIClient(timeout=10, max_retries=2)
    
    # Probar conexión
    if not api_client.test_connection():
        print("❌ Error: No se pudo conectar con la API")
        return False
    
    print("✅ Conexión exitosa con la API de Mercadona")
    
    # Obtener productos de la subcategoría
    data = api_client.get_subcategory_products(161)
    
    if not data:
        print("❌ No se pudieron obtener datos de la subcategoría")
        return False
    
    print(f"✅ Datos obtenidos correctamente")
    print(f"📂 Nombre: {data.get('name', 'Sin nombre')}")
    print(f"🔢 ID: {data.get('id')}")
    
    # Contar productos
    total_products = 0
    categories = data.get('categories', [])
    
    print(f"📊 Subcategorías anidadas encontradas: {len(categories)}")
    
    for i, category in enumerate(categories, 1):
        products = category.get('products', [])
        cat_name = category.get('name', f'Categoría {i}')
        print(f"   {i}. {cat_name}: {len(products)} productos")
        
        # Mostrar algunos productos de ejemplo
        if products:
            print(f"      Ejemplos:")
            for j, product in enumerate(products[:3], 1):
                name = product.get('display_name', 'Sin nombre')
                price = product.get('price_instructions', {}).get('unit_price', 'N/A')
                print(f"        {j}. {name} - {price}€")
        
        total_products += len(products)
    
    print(f"🛍️  Total productos: {total_products}")
    
    # Crear extractor y probar extracción
    print("\n🔄 Probando extracción de información...")
    extractor = MercadonaProductExtractor(api_client)
    
    all_products = []
    for category in categories:
        products = category.get('products', [])
        for product in products:
            # Añadir información de contexto
            product['category_id'] = 18  # Agua y refrescos
            product['category_name'] = 'Agua y refrescos'
            product['subcategory_id'] = 161
            product['subcategory_name'] = 'Tónica y bitter'
            product['nested_category_id'] = category.get('id')
            product['nested_category_name'] = category.get('name', '')
            
            extracted = extractor.extract_product_info(product)
            if extracted:
                all_products.append(extracted)
    
    print(f"✅ Extraídos {len(all_products)} productos")
    
    # Mostrar estadísticas de algunos campos
    if all_products:
        print("\n📈 Estadísticas:")
        
        # Precios
        prices = [float(p['unit_price']) for p in all_products if p.get('unit_price') and p['unit_price'] != 'N/A']
        if prices:
            print(f"💰 Precios: min={min(prices):.2f}€, max={max(prices):.2f}€, avg={sum(prices)/len(prices):.2f}€")
        
        # Marcas/packaging
        packages = [p['packaging'] for p in all_products if p.get('packaging')]
        if packages:
            unique_packages = set(packages)
            print(f"📦 Tipos de empaque: {', '.join(unique_packages)}")
        
        # Productos en oferta
        decreased = [p for p in all_products if p.get('price_decreased')]
        print(f"🔥 Productos con precio reducido: {len(decreased)}")
    
    # Guardar muestra en archivo
    output_file = "test_productos_subcategoria_161.json"
    success = extractor.save_to_json(output_file)
    
    if success:
        print(f"💾 Datos guardados en: {output_file}")
    
    # Limpiar recursos
    api_client.close()
    
    return True


def test_category_structure():
    """Prueba la estructura de categorías principales."""
    print("\n🧪 Probando estructura de categorías principales...")
    
    api_client = MercadonaAPIClient(timeout=10, max_retries=2)
    
    # Probar con categoría "Agua y refrescos" (ID 18)
    data = api_client.get_category_products(18)
    
    if not data:
        print("❌ No se pudieron obtener datos de la categoría")
        return False
    
    print(f"✅ Categoría obtenida: {data.get('name', 'Sin nombre')}")
    
    subcategories = data.get('categories', [])
    print(f"📂 Subcategorías disponibles: {len(subcategories)}")
    
    for i, subcat in enumerate(subcategories, 1):
        name = subcat.get('name', f'Subcategoría {i}')
        subcat_id = subcat.get('id')
        print(f"   {i}. {name} (ID: {subcat_id})")
    
    api_client.close()
    return True


if __name__ == "__main__":
    print("🚀 Iniciando pruebas del scraper de Mercadona\n")
    
    # Ejecutar pruebas
    try:
        test1_ok = test_category_structure()
        test2_ok = test_single_subcategory()
        
        if test1_ok and test2_ok:
            print("\n✅ Todas las pruebas completadas exitosamente!")
            print("El scraper está listo para usar.")
        else:
            print("\n❌ Algunas pruebas fallaron.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Pruebas canceladas por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        sys.exit(1)