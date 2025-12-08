#!/usr/bin/env python3
"""
Script para cargar productos de Mercadona en la base de datos.

Uso:
    uv run python load_products.py productos_mercadona.json
    uv run python load_products.py --summary
    uv run python load_products.py --clear-old 7
"""

import sys
import argparse
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mercagasto.config.settings import get_database_config
from mercagasto.storage.product_loader import MercadonaProductLoader


def load_products(json_file: str, batch_size: int = 100):
    """Carga productos desde archivo JSON."""
    
    if not Path(json_file).exists():
        print(f"❌ Archivo {json_file} no encontrado")
        return
    
    print(f"🚀 Cargando productos desde: {json_file}")
    
    try:
        db_config = get_database_config()
        
        with MercadonaProductLoader(db_config) as loader:
            stats = loader.load_products_from_json(json_file, batch_size)
            
        print(f"\n🎯 CARGA COMPLETADA:")
        print(f"   📦 Total productos: {stats['total_products']}")
        print(f"   ✅ Insertados: {stats['inserted']}")
        print(f"   🔄 Actualizados: {stats['updated']}")
        print(f"   ⚠️  Omitidos: {stats['skipped']}")
        print(f"   ❌ Errores: {stats['errors']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def show_summary():
    """Muestra resumen de la base de datos."""
    
    print("📊 Obteniendo resumen de la base de datos...")
    
    try:
        db_config = get_database_config()
        
        with MercadonaProductLoader(db_config) as loader:
            summary = loader.get_products_summary()
            
        print(f"\n📈 RESUMEN DE BASE DE DATOS:")
        print(f"   📦 Total productos: {summary['total_productos']}")
        print(f"   ✅ Productos publicados: {summary['productos_publicados']}")
        print(f"   💰 Productos en oferta: {summary['productos_en_oferta']}")
        print(f"   📂 Total categorías: {summary['total_categorias']}")
        print(f"   📂 Total subcategorías: {summary['total_subcategorias']}")
        print(f"   📅 Primera extracción: {summary['primera_extraccion']}")
        print(f"   📅 Última extracción: {summary['ultima_extraccion']}")
        
        if summary.get('top_categorias'):
            print(f"\n🏆 TOP CATEGORÍAS:")
            for cat in summary['top_categorias']:
                print(f"   • {cat['categoria']}: {cat['productos']} productos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def clear_old_products(days_old: int = 7):
    """Elimina productos antiguos."""
    
    print(f"🗑️  Eliminando productos mayores a {days_old} días...")
    
    try:
        db_config = get_database_config()
        
        with MercadonaProductLoader(db_config) as loader:
            deleted_count = loader.clear_old_products(days_old)
            
        print(f"✅ Eliminados {deleted_count} productos antiguos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Cargador de productos de Mercadona")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('json_file', nargs='?', help="Archivo JSON con productos")
    group.add_argument('--summary', action='store_true', help="Mostrar resumen de la BD")
    group.add_argument('--clear-old', type=int, metavar='DAYS', help="Eliminar productos antiguos")
    
    parser.add_argument('--batch-size', type=int, default=100, 
                       help="Tamaño del lote para carga (default: 100)")
    
    args = parser.parse_args()
    
    if args.json_file:
        load_products(args.json_file, args.batch_size)
    elif args.summary:
        show_summary()
    elif args.clear_old:
        clear_old_products(args.clear_old)


if __name__ == '__main__':
    main()