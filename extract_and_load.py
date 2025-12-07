#!/usr/bin/env python3
"""
Script completo para extraer y cargar productos de Mercadona.

Este script automatiza todo el proceso:
1. Extrae productos de la API de Mercadona
2. Los carga en la base de datos
3. Proporciona estadísticas y resumen
"""

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent if current_dir.name == 'src' else current_dir
sys.path.insert(0, str(root_dir))

from src.mercagasto.processors.mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from src.mercagasto.storage import MercadonaProductLoader
from src.mercagasto.config import setup_logging, get_logger, DatabaseConfig

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def extract_and_load_products(category_ids: Optional[list] = None,
                            output_file: Optional[str] = None,
                            keep_json: bool = True,
                            delay: float = 2.0,
                            batch_size: int = 100,
                            clear_old: bool = True,
                            clear_days: int = 7) -> bool:
    """
    Proceso completo de extracción y carga de productos.
    
    Args:
        category_ids: Lista de IDs de categorías (None para todas)
        output_file: Archivo JSON de salida (None para temporal)
        keep_json: Si mantener el archivo JSON después de la carga
        delay: Pausa entre categorías en segundos
        batch_size: Tamaño del lote para commits en BD
        clear_old: Si eliminar productos antiguos antes de la carga
        clear_days: Días de antigüedad para productos obsoletos
        
    Returns:
        True si todo el proceso fue exitoso
    """
    temp_file = None
    
    try:
        logger.info("🚀 INICIANDO PROCESO COMPLETO DE EXTRACCIÓN Y CARGA")
        logger.info("=" * 60)
        
        # ===== FASE 1: EXTRACCIÓN =====
        logger.info("📡 FASE 1: EXTRACCIÓN DE PRODUCTOS")
        
        # Determinar archivo de salida
        if not output_file:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.json', 
                prefix='mercadona_productos_', 
                delete=False
            )
            temp_file.close()
            output_file = temp_file.name
            logger.info(f"   📄 Usando archivo temporal: {output_file}")
        else:
            logger.info(f"   📄 Archivo de salida: {output_file}")
        
        # Cargar categorías si no se especificaron
        if not category_ids:
            import json
            categories_file = root_dir / "src" / "mercagasto" / "storage" / "data" / "categorias.json"
            
            try:
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                category_ids = [cat['id'] for cat in data.get('results', [])]
                logger.info(f"   📂 Cargadas {len(category_ids)} categorías desde JSON")
            except Exception as e:
                logger.error(f"   ❌ Error cargando categorías: {e}")
                return False
        else:
            logger.info(f"   📂 Procesando {len(category_ids)} categorías específicas")
        
        # Crear cliente API y extractor
        api_client = MercadonaAPIClient(lang="es", timeout=30, max_retries=3)
        
        if not api_client.test_connection():
            logger.error("   ❌ No se pudo conectar con la API de Mercadona")
            return False
        
        extractor = MercadonaProductExtractor(api_client)
        
        # Extraer productos
        products = extractor.extract_all_products(
            category_ids=category_ids,
            delay_between_categories=delay
        )
        
        if not products:
            logger.error("   ❌ No se extrajeron productos")
            return False
        
        # Guardar JSON
        if not extractor.save_to_json(output_file):
            logger.error("   ❌ Error guardando archivo JSON")
            return False
        
        logger.info(f"   ✅ Extracción completada: {len(products)} productos")
        
        # Limpiar recursos
        api_client.close()
        
        # ===== FASE 2: CARGA EN BASE DE DATOS =====
        logger.info("\n💾 FASE 2: CARGA EN BASE DE DATOS")
        
        # Configurar base de datos
        db_config = DatabaseConfig.from_env()
        logger.info(f"   🗄️  Conectando a: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # Cargar productos
        with MercadonaProductLoader(db_config) as loader:
            
            # Limpiar productos antiguos si se solicita
            if clear_old:
                logger.info(f"   🗑️  Eliminando productos antiguos (>{clear_days} días)...")
                deleted = loader.clear_old_products(clear_days)
                logger.info(f"   ✅ {deleted} productos eliminados")
            
            # Cargar productos
            stats = loader.load_products_from_json(output_file, batch_size)
            
            if stats['total_products'] == 0:
                logger.error("   ❌ No se encontraron productos para cargar")
                return False
            
            success_rate = ((stats['inserted'] + stats['updated']) / stats['total_products']) * 100
            
            if success_rate < 70:
                logger.error(f"   ❌ Tasa de éxito muy baja: {success_rate:.1f}%")
                return False
            
            logger.info(f"   ✅ Carga completada: {success_rate:.1f}% éxito")
            
            # ===== FASE 3: RESUMEN FINAL =====
            logger.info("\n📊 FASE 3: RESUMEN FINAL")
            
            summary = loader.get_products_summary()
            
            print("\n" + "="*60)
            print("🎯 PROCESO COMPLETADO EXITOSAMENTE")
            print("="*60)
            print(f"📦 Total productos en BD: {summary['total_productos']:,}")
            print(f"✅ Productos publicados: {summary['productos_publicados']:,}")
            print(f"🔥 Productos en oferta: {summary['productos_en_oferta']:,}")
            print(f"📂 Categorías: {summary['total_categorias']}")
            print(f"📁 Subcategorías: {summary['total_subcategorias']}")
            
            if summary['top_categorias']:
                print(f"\n🏆 TOP 5 CATEGORÍAS:")
                for i, cat in enumerate(summary['top_categorias'], 1):
                    print(f"   {i}. {cat['categoria']}: {cat['productos']:,} productos")
            
            print(f"\n📄 Archivo JSON: {output_file}")
            if not keep_json and temp_file:
                print("   (será eliminado automáticamente)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante el proceso: {e}")
        return False
        
    finally:
        # Limpiar archivo temporal si no se quiere mantener
        if temp_file and not keep_json:
            try:
                Path(temp_file.name).unlink(missing_ok=True)
                logger.debug("Archivo temporal eliminado")
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Extractor y cargador completo de productos de Mercadona",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python extract_and_load.py                                      # Proceso completo automático
  python extract_and_load.py --categories 18,19,20               # Solo ciertas categorías
  python extract_and_load.py --output productos.json             # Mantener archivo JSON
  python extract_and_load.py --delay 1.0 --batch-size 50         # Configurar rendimiento
  python extract_and_load.py --no-clear-old                      # No limpiar productos antiguos
        """
    )
    
    parser.add_argument(
        '--categories',
        type=str,
        help='Lista de IDs de categorías separados por comas (ej: 1,2,3)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Archivo JSON de salida (default: temporal)'
    )
    
    parser.add_argument(
        '--keep-json',
        action='store_true',
        default=True,
        help='Mantener archivo JSON después de la carga (default: True)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Pausa entre categorías en segundos (default: 2.0)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamaño del lote para commits en BD (default: 100)'
    )
    
    parser.add_argument(
        '--no-clear-old',
        action='store_true',
        help='No eliminar productos antiguos antes de cargar'
    )
    
    parser.add_argument(
        '--clear-days',
        type=int,
        default=7,
        help='Días de antigüedad para productos obsoletos (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Procesar categorías específicas si se proporcionaron
    category_ids = None
    if args.categories:
        try:
            category_ids = [int(x.strip()) for x in args.categories.split(',')]
            logger.info(f"Procesando categorías específicas: {category_ids}")
        except ValueError as e:
            logger.error(f"Error en formato de categorías: {e}")
            sys.exit(1)
    
    # Ejecutar proceso completo
    success = extract_and_load_products(
        category_ids=category_ids,
        output_file=args.output,
        keep_json=args.keep_json,
        delay=args.delay,
        batch_size=args.batch_size,
        clear_old=not args.no_clear_old,
        clear_days=args.clear_days
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()