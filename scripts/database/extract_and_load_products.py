#!/usr/bin/env python3
"""
Script completo para extraer productos de Mercadona: API → JSON → Base de datos.

Uso:
    uv run python extract_and_load_products.py --categories 1,2,3
    uv run python extract_and_load_products.py --extract-only
    uv run python extract_and_load_products.py --load-only productos.json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mercagasto.processors.mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from mercagasto.config.settings import get_database_config
from mercagasto.storage.product_loader import MercadonaProductLoader


def extract_products_from_api(category_ids: list, output_file: str = None):
    """
    Extrae productos de la API de Mercadona por categorías.
    
    Args:
        category_ids: Lista de IDs de categorías
        output_file: Archivo donde guardar los productos (JSON)
    """
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"productos_mercadona_{timestamp}.json"
    
    print(f"🌐 Extrayendo productos de {len(category_ids)} categorías desde API...")
    print(f"📂 Archivo de salida: {output_file}")
    
    try:
        # Crear cliente de API
        api_client = MercadonaAPIClient()
        
        # Probar conexión
        if not api_client.test_connection():
            print("❌ No se puede conectar con la API de Mercadona")
            return False
        
        # Crear extractor
        extractor = MercadonaProductExtractor(api_client)
        
        # Extraer productos de todas las categorías (tratándolas como subcategorías)
        all_products = extractor.extract_all_products(category_ids, treat_as_subcategories=True)
        
        if not all_products:
            print("⚠️  No se encontraron productos")
            return False
        
        # Preparar datos para JSON
        output_data = {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "categories_processed": category_ids,
                "total_products": len(all_products),
                "extractor_stats": extractor.extraction_stats
            },
            "products": all_products
        }
        
        # Guardar en JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Extracción completada:")
        print(f"   📦 Total productos: {len(all_products)}")
        print(f"   📄 Archivo generado: {output_file}")
        
        # Cerrar conexión
        api_client.close()
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")
        return False


def load_products_to_database(json_file: str):
    """
    Carga productos desde JSON a la base de datos.
    
    Args:
        json_file: Archivo JSON con productos
    """
    
    if not Path(json_file).exists():
        print(f"❌ Archivo {json_file} no encontrado")
        return False
    
    print(f"💾 Cargando productos desde {json_file} a la base de datos...")
    
    try:
        db_config = get_database_config()
        
        with MercadonaProductLoader(db_config) as loader:
            stats = loader.load_products_from_json(json_file)
            
        print(f"✅ Carga completada:")
        print(f"   📦 Total productos: {stats['total_products']}")
        print(f"   ✅ Insertados: {stats['inserted']}")
        print(f"   🔄 Actualizados: {stats['updated']}")
        print(f"   ⚠️  Omitidos: {stats['skipped']}")
        print(f"   ❌ Errores: {stats['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la carga: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Extractor y cargador completo de productos Mercadona")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--categories', type=str, 
                      help="IDs de categorías separados por comas (ej: 1,2,3)")
    group.add_argument('--extract-only', action='store_true',
                      help="Solo extraer de API (no cargar a BD)")
    group.add_argument('--load-only', type=str, metavar='JSON_FILE',
                      help="Solo cargar desde JSON a BD")
    
    parser.add_argument('--output', type=str,
                       help="Archivo de salida para la extracción")
    parser.add_argument('--no-load', action='store_true',
                       help="No cargar a BD después de extraer")
    
    args = parser.parse_args()
    
    if args.categories:
        # Flujo completo: extraer y cargar
        try:
            category_ids = [int(x.strip()) for x in args.categories.split(',')]
        except ValueError:
            print("❌ Error: Las categorías deben ser números separados por comas")
            sys.exit(1)
        
        # Extraer de API
        json_file = extract_products_from_api(category_ids, args.output)
        
        if json_file and not args.no_load:
            # Cargar a BD
            success = load_products_to_database(json_file)
            if success:
                print(f"\n🎉 ¡Proceso completo exitoso!")
        
    elif args.extract_only:
        print("⚠️  Especifica --categories para extraer")
        
    elif args.load_only:
        # Solo cargar
        success = load_products_to_database(args.load_only)
        if success:
            print(f"\n🎉 ¡Carga exitosa!")


if __name__ == '__main__':
    main()