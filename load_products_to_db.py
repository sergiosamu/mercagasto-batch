#!/usr/bin/env python3
"""
Script para cargar productos de Mercadona en la base de datos.

Este script toma el archivo JSON generado por el scraper de productos
y lo carga en la base de datos PostgreSQL.
"""

import argparse
import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent if current_dir.name == 'src' else current_dir
sys.path.insert(0, str(root_dir))

from src.mercagasto.storage import MercadonaProductLoader
from src.mercagasto.config import setup_logging, get_logger, DatabaseConfig

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def load_products_to_database(json_file: str, 
                            batch_size: int = 100,
                            clear_old: bool = False,
                            clear_days: int = 7) -> bool:
    """
    Carga productos en la base de datos desde un archivo JSON.
    
    Args:
        json_file: Ruta al archivo JSON con productos
        batch_size: Tamaño del lote para commits
        clear_old: Si eliminar productos antiguos antes de la carga
        clear_days: Días de antigüedad para considerar productos obsoletos
        
    Returns:
        True si la carga fue exitosa
    """
    try:
        # Verificar que el archivo existe
        if not Path(json_file).exists():
            logger.error(f"❌ El archivo {json_file} no existe")
            return False
        
        logger.info(f"📂 Archivo JSON: {json_file}")
        logger.info(f"📦 Tamaño de lote: {batch_size}")
        
        # Configurar base de datos
        db_config = DatabaseConfig.from_env()
        logger.info(f"🗄️  Base de datos: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # Crear loader y conectar
        with MercadonaProductLoader(db_config) as loader:
            
            # Limpiar productos antiguos si se solicita
            if clear_old:
                logger.info(f"🗑️  Eliminando productos antiguos (>{clear_days} días)...")
                deleted = loader.clear_old_products(clear_days)
                logger.info(f"   ✅ {deleted} productos eliminados")
            
            # Cargar productos
            stats = loader.load_products_from_json(json_file, batch_size)
            
            # Verificar resultados
            if stats['total_products'] == 0:
                logger.warning("⚠️  No se encontraron productos para cargar")
                return False
            
            success_rate = ((stats['inserted'] + stats['updated']) / stats['total_products']) * 100
            
            if success_rate >= 90:
                logger.info(f"✅ Carga exitosa: {success_rate:.1f}% productos procesados correctamente")
                return True
            elif success_rate >= 70:
                logger.warning(f"⚠️  Carga parcialmente exitosa: {success_rate:.1f}% productos procesados")
                return True
            else:
                logger.error(f"❌ Carga con problemas: solo {success_rate:.1f}% productos procesados")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error durante la carga: {e}")
        return False


def show_database_summary() -> bool:
    """
    Muestra un resumen de los productos en la base de datos.
    
    Returns:
        True si se pudo obtener el resumen
    """
    try:
        db_config = DatabaseConfig.from_env()
        
        with MercadonaProductLoader(db_config) as loader:
            summary = loader.get_products_summary()
            
            print("\n📊 RESUMEN DE PRODUCTOS EN BASE DE DATOS:")
            print("=" * 50)
            print(f"📦 Total productos: {summary['total_productos']:,}")
            print(f"✅ Productos publicados: {summary['productos_publicados']:,}")
            print(f"🔥 Productos en oferta: {summary['productos_en_oferta']:,}")
            print(f"📂 Categorías: {summary['total_categorias']}")
            print(f"📁 Subcategorías: {summary['total_subcategorias']}")
            
            if summary['primera_extraccion'] and summary['ultima_extraccion']:
                print(f"📅 Primera extracción: {summary['primera_extraccion']}")
                print(f"📅 Última extracción: {summary['ultima_extraccion']}")
            
            if summary['top_categorias']:
                print("\n🏆 TOP CATEGORÍAS:")
                for i, cat in enumerate(summary['top_categorias'], 1):
                    print(f"   {i}. {cat['categoria']}: {cat['productos']:,} productos")
            
            return True
            
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        return False


def clear_old_products(days: int = 7) -> bool:
    """
    Elimina productos antiguos de la base de datos.
    
    Args:
        days: Días de antigüedad
        
    Returns:
        True si se eliminaron correctamente
    """
    try:
        db_config = DatabaseConfig.from_env()
        
        with MercadonaProductLoader(db_config) as loader:
            deleted = loader.clear_old_products(days)
            
            if deleted > 0:
                logger.info(f"✅ {deleted} productos eliminados")
            else:
                logger.info("ℹ️  No había productos antiguos para eliminar")
            
            return True
            
    except Exception as e:
        logger.error(f"Error eliminando productos antiguos: {e}")
        return False


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Cargador de productos de Mercadona en base de datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python load_products_to_db.py productos.json                    # Cargar productos
  python load_products_to_db.py productos.json --batch-size 50    # Lotes de 50
  python load_products_to_db.py productos.json --clear-old        # Limpiar antiguos antes
  python load_products_to_db.py --summary                         # Ver resumen de BD
  python load_products_to_db.py --clear-old-only --days 14        # Solo limpiar antiguos
        """
    )
    
    parser.add_argument(
        'json_file',
        nargs='?',
        help='Archivo JSON con productos a cargar'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamaño del lote para commits (default: 100)'
    )
    
    parser.add_argument(
        '--clear-old',
        action='store_true',
        help='Eliminar productos antiguos antes de cargar'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Días de antigüedad para productos obsoletos (default: 7)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Mostrar resumen de productos en base de datos'
    )
    
    parser.add_argument(
        '--clear-old-only',
        action='store_true',
        help='Solo eliminar productos antiguos (no cargar)'
    )
    
    args = parser.parse_args()
    
    # Modo solo resumen
    if args.summary:
        success = show_database_summary()
        sys.exit(0 if success else 1)
    
    # Modo solo limpiar antiguos
    if args.clear_old_only:
        success = clear_old_products(args.days)
        sys.exit(0 if success else 1)
    
    # Modo carga de productos
    if not args.json_file:
        parser.error("Se requiere especificar el archivo JSON o usar --summary/--clear-old-only")
    
    success = load_products_to_database(
        json_file=args.json_file,
        batch_size=args.batch_size,
        clear_old=args.clear_old,
        clear_days=args.days
    )
    
    if success:
        # Mostrar resumen después de la carga
        print("\n" + "="*60)
        show_database_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()