#!/usr/bin/env python3
"""
Script para extraer productos de todas las categorías de Mercadona.

Este script utiliza la API de Mercadona para obtener información completa
de productos de todas las categorías y subcategorías disponibles.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Añadir el directorio raíz al path para importaciones
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from src.mercagasto.processors.mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from src.mercagasto.config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def load_categories_from_json(json_file: str) -> List[int]:
    """
    Carga los IDs de categorías desde el archivo JSON.
    
    Args:
        json_file: Ruta al archivo categorias.json
        
    Returns:
        Lista de IDs de categorías
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        category_ids = []
        for category in data.get('results', []):
            category_id = category.get('id')
            if category_id:
                category_ids.append(category_id)
        
        logger.info(f"Cargados {len(category_ids)} IDs de categorías desde {json_file}")
        return sorted(category_ids)
        
    except Exception as e:
        logger.error(f"Error cargando categorías desde {json_file}: {e}")
        return []


def extract_all_products(output_file: str = None, 
                        category_ids: List[int] = None,
                        delay: float = 2.0,
                        timeout: int = 30,
                        max_retries: int = 3) -> bool:
    """
    Extrae todos los productos de las categorías especificadas.
    
    Args:
        output_file: Archivo donde guardar los resultados
        category_ids: Lista de IDs de categorías (si None, carga desde JSON)
        delay: Pausa entre categorías en segundos
        timeout: Timeout para peticiones HTTP
        max_retries: Número máximo de reintentos
        
    Returns:
        True si la extracción fue exitosa
    """
    try:
        # Cargar categorías si no se especificaron
        if not category_ids:
            categories_file = root_dir / "src" / "mercagasto" / "storage" / "data" / "categorias.json"
            category_ids = load_categories_from_json(str(categories_file))
            
            if not category_ids:
                logger.error("No se pudieron cargar los IDs de categorías")
                return False
        
        # Configurar archivo de salida por defecto
        if not output_file:
            timestamp = Path(__file__).parent / f"mercadona_productos_{int(__import__('time').time())}.json"
            output_file = str(timestamp)
        
        logger.info(f"🎯 Configuración de extracción:")
        logger.info(f"   📂 Categorías: {len(category_ids)}")
        logger.info(f"   ⏱️  Pausa entre categorías: {delay}s")
        logger.info(f"   🔄 Timeout: {timeout}s")
        logger.info(f"   🔁 Reintentos máximos: {max_retries}")
        logger.info(f"   💾 Archivo de salida: {output_file}")
        
        # Crear cliente API
        api_client = MercadonaAPIClient(
            lang="es",
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Probar conexión
        if not api_client.test_connection():
            logger.error("❌ No se pudo conectar con la API de Mercadona")
            return False
        
        # Crear extractor
        extractor = MercadonaProductExtractor(api_client)
        
        # Extraer productos
        logger.info("🚀 Iniciando extracción de productos...")
        products = extractor.extract_all_products(
            category_ids=category_ids,
            delay_between_categories=delay
        )
        
        if not products:
            logger.error("❌ No se extrajeron productos")
            return False
        
        # Guardar resultados
        success = extractor.save_to_json(output_file)
        
        if success:
            logger.info(f"✅ Extracción completada exitosamente")
            logger.info(f"   📊 Total productos: {len(products)}")
            logger.info(f"   💾 Guardado en: {output_file}")
            
            # Mostrar estadísticas por categoría
            category_stats = {}
            for product in products:
                cat_id = product.get('category_id')
                cat_name = product.get('category_name', f'Categoría {cat_id}')
                key = f"{cat_name} ({cat_id})"
                
                if key not in category_stats:
                    category_stats[key] = 0
                category_stats[key] += 1
            
            logger.info("📈 Productos por categoría:")
            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {category}: {count} productos")
        else:
            logger.error("❌ Error guardando los resultados")
        
        # Limpiar recursos
        api_client.close()
        
        return success
        
    except KeyboardInterrupt:
        logger.info("🛑 Extracción cancelada por el usuario")
        return False
    except Exception as e:
        logger.error(f"❌ Error durante la extracción: {e}")
        return False


def extract_single_category(category_id: int, output_file: str = None) -> bool:
    """
    Extrae productos de una sola categoría.
    
    Args:
        category_id: ID de la categoría
        output_file: Archivo donde guardar los resultados
        
    Returns:
        True si la extracción fue exitosa
    """
    if not output_file:
        output_file = f"mercadona_categoria_{category_id}.json"
    
    return extract_all_products(
        output_file=output_file,
        category_ids=[category_id],
        delay=0.5
    )


def list_categories() -> bool:
    """
    Lista todas las categorías disponibles.
    
    Returns:
        True si se listaron correctamente
    """
    try:
        categories_file = root_dir / "src" / "mercagasto" / "storage" / "data" / "categorias.json"
        
        with open(categories_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        categories = data.get('results', [])
        
        print("📂 Categorías disponibles:")
        print("-" * 50)
        
        for category in sorted(categories, key=lambda x: x.get('order', 0)):
            cat_id = category.get('id')
            name = category.get('name', 'Sin nombre')
            order = category.get('order', 0)
            subcats = len(category.get('categories', []))
            
            print(f"{cat_id:3d} | {name:<35} | Orden: {order:3d} | Subcategorías: {subcats}")
        
        print("-" * 50)
        print(f"Total: {len(categories)} categorías")
        
        return True
        
    except Exception as e:
        logger.error(f"Error listando categorías: {e}")
        return False


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Extractor de productos de Mercadona",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python mercadona_product_scraper.py                    # Extraer todas las categorías
  python mercadona_product_scraper.py --list             # Listar categorías disponibles
  python mercadona_product_scraper.py --category 18      # Extraer solo categoría 18
  python mercadona_product_scraper.py --output productos.json  # Especificar archivo de salida
  python mercadona_product_scraper.py --delay 1.0        # Cambiar pausa entre categorías
        """
    )
    
    parser.add_argument(
        '--list', 
        action='store_true',
        help='Lista todas las categorías disponibles'
    )
    
    parser.add_argument(
        '--category', 
        type=int,
        help='Extraer productos de una sola categoría (ID)'
    )
    
    parser.add_argument(
        '--categories',
        type=str,
        help='Lista de IDs de categorías separados por comas (ej: 1,2,3)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Archivo de salida para guardar los productos (JSON)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Pausa entre categorías en segundos (default: 2.0)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout para peticiones HTTP en segundos (default: 30)'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Número máximo de reintentos (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Modo listado
    if args.list:
        success = list_categories()
        sys.exit(0 if success else 1)
    
    # Modo categoría única
    if args.category:
        success = extract_single_category(args.category, args.output)
        sys.exit(0 if success else 1)
    
    # Modo categorías específicas
    category_ids = None
    if args.categories:
        try:
            category_ids = [int(x.strip()) for x in args.categories.split(',')]
            logger.info(f"Procesando categorías específicas: {category_ids}")
        except ValueError as e:
            logger.error(f"Error en formato de categorías: {e}")
            sys.exit(1)
    
    # Modo extracción completa o de categorías específicas
    success = extract_all_products(
        output_file=args.output,
        category_ids=category_ids,
        delay=args.delay,
        timeout=args.timeout,
        max_retries=args.retries
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()