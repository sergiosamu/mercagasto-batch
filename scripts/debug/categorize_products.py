#!/usr/bin/env python3
"""
Script para categorizar productos de tickets usando el catálogo de Mercadona.

Este script asocia los productos de los tickets con las categorías del catálogo
de Mercadona para permitir informes por categorías.
"""

import argparse
import sys
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent if current_dir.name == 'src' else current_dir
sys.path.insert(0, str(root_dir))

from src.mercagasto.processors.product_matcher import ProductMatcher
from src.mercagasto.storage import PostgreSQLTicketStorage
from src.mercagasto.config import setup_logging, get_logger, AppConfig

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def categorize_products(batch_size: int = 100, recategorize: bool = False) -> bool:
    """
    Categoriza productos de tickets usando el catálogo de Mercadona.
    
    Args:
        batch_size: Tamaño del lote para procesamiento
        recategorize: Si recategorizar productos ya categorizados
        
    Returns:
        True si el proceso fue exitoso
    """
    try:
        # Configurar aplicación
        config = AppConfig.from_env()
        storage = PostgreSQLTicketStorage(config.database)
        
        logger.info("🔗 CATEGORIZADOR DE PRODUCTOS")
        logger.info("=" * 50)
        logger.info(f"🗄️  Base de datos: {config.database.host}:{config.database.port}/{config.database.database}")
        logger.info(f"📦 Tamaño de lote: {batch_size}")
        logger.info(f"🔄 Recategorizar: {'Sí' if recategorize else 'No'}")
        
        # Crear matcher
        matcher = ProductMatcher(storage)
        
        # Verificar que hay datos del catálogo
        logger.info("📚 Cargando catálogo de Mercadona...")
        matcher.load_catalog_data()
        
        if not matcher.mercadona_products:
            logger.error("❌ No se encontraron productos del catálogo de Mercadona")
            logger.info("💡 Asegúrate de haber ejecutado el scraper de productos primero:")
            logger.info("   python extract_and_load.py")
            return False
        
        # Si se solicita recategorizar, limpiar categorías existentes
        if recategorize:
            logger.info("🗑️  Limpiando categorizaciones existentes...")
            
            with storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE productos SET
                        mercadona_producto_id = NULL,
                        categoria_id = NULL,
                        subcategoria_id = NULL,
                        categoria_detectada = NULL,
                        subcategoria_detectada = NULL,
                        confidence_score = NULL,
                        matching_method = NULL
                """)
                cleared_count = cursor.rowcount
                conn.commit()
                cursor.close()
            
            logger.info(f"   ✅ {cleared_count} productos limpiados")
        
        # Procesar productos
        stats = matcher.process_all_products(batch_size)
        
        if stats['total_processed'] == 0:
            logger.info("ℹ️  No hay productos para categorizar")
            return True
        
        # Verificar resultados
        success_rate = 0
        if stats['total_processed'] > 0:
            successful = (stats['total_processed'] - stats['no_matches'] - stats['errors'])
            success_rate = (successful / stats['total_processed']) * 100
        
        if success_rate >= 70:
            logger.info(f"✅ Categorización exitosa: {success_rate:.1f}% productos categorizados")
            return True
        elif success_rate >= 50:
            logger.warning(f"⚠️  Categorización parcial: {success_rate:.1f}% productos categorizados")
            return True
        else:
            logger.error(f"❌ Categorización con problemas: solo {success_rate:.1f}% categorizados")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error durante la categorización: {e}")
        return False


def show_categorization_stats() -> bool:
    """
    Muestra estadísticas de la categorización actual.
    
    Returns:
        True si se pudieron obtener las estadísticas
    """
    try:
        config = AppConfig.from_env()
        storage = PostgreSQLTicketStorage(config.database)
        
        with storage.get_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_productos,
                    COUNT(CASE WHEN categoria_id IS NOT NULL THEN 1 END) as categorizados,
                    COUNT(CASE WHEN mercadona_producto_id IS NOT NULL THEN 1 END) as con_producto_mercadona,
                    ROUND(AVG(confidence_score), 3) as confidence_promedio
                FROM productos
            """)
            
            row = cursor.fetchone()
            total, categorizados, con_producto, confidence_avg = row
            
            print("\n📊 ESTADÍSTICAS DE CATEGORIZACIÓN:")
            print("=" * 50)
            print(f"📦 Total productos: {total:,}")
            print(f"✅ Categorizados: {categorizados:,} ({(categorizados/total*100):.1f}%)")
            print(f"🛍️  Con producto Mercadona: {con_producto:,}")
            print(f"🎯 Confianza promedio: {confidence_avg:.3f}" if confidence_avg else "🎯 Confianza promedio: N/A")
            
            # Estadísticas por método de matching
            cursor.execute("""
                SELECT matching_method, COUNT(*) as count, ROUND(AVG(confidence_score), 3) as avg_confidence
                FROM productos 
                WHERE matching_method IS NOT NULL
                GROUP BY matching_method
                ORDER BY count DESC
            """)
            
            methods = cursor.fetchall()
            
            if methods:
                print("\n🔍 POR MÉTODO DE MATCHING:")
                for method, count, avg_conf in methods:
                    print(f"   {method}: {count:,} productos (confianza: {avg_conf:.3f})")
            
            # Top categorías
            cursor.execute("""
                SELECT categoria_detectada, COUNT(*) as count, ROUND(SUM(precio_total), 2) as total_gasto
                FROM productos 
                WHERE categoria_detectada IS NOT NULL
                GROUP BY categoria_detectada
                ORDER BY total_gasto DESC
                LIMIT 10
            """)
            
            categories = cursor.fetchall()
            
            if categories:
                print("\n🏆 TOP 10 CATEGORÍAS POR GASTO:")
                for i, (categoria, count, gasto) in enumerate(categories, 1):
                    print(f"   {i:2d}. {categoria}: {count:,} productos - {gasto:,.2f}€")
            
            # Productos sin categorizar (ejemplos)
            cursor.execute("""
                SELECT descripcion, precio_total, cantidad
                FROM productos 
                WHERE categoria_id IS NULL
                ORDER BY precio_total DESC
                LIMIT 5
            """)
            
            uncategorized = cursor.fetchall()
            
            if uncategorized:
                print("\n❓ PRODUCTOS SIN CATEGORIZAR (ejemplos):")
                for desc, precio, cant in uncategorized:
                    print(f"   • {desc} - {precio:.2f}€ (x{cant})")
            
            cursor.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return False


def generate_category_report(output_file: str = None) -> bool:
    """
    Genera un informe de gastos por categorías.
    
    Args:
        output_file: Archivo de salida (opcional)
        
    Returns:
        True si se generó correctamente
    """
    try:
        config = AppConfig.from_env()
        storage = PostgreSQLTicketStorage(config.database)
        
        logger.info("📊 Generando informe por categorías...")
        
        with storage.get_connection() as conn:
            cursor = conn.cursor()
            
            # Informe por categorías
            cursor.execute("""
                SELECT 
                    c.nombre as categoria,
                    COUNT(DISTINCT p.ticket_id) as num_tickets,
                    COUNT(p.id) as num_productos,
                    SUM(p.cantidad) as cantidad_total,
                    ROUND(SUM(p.precio_total), 2) as gasto_total,
                    ROUND(AVG(p.precio_total), 2) as precio_promedio,
                    ROUND(AVG(p.confidence_score), 2) as confidence_promedio,
                    MIN(t.fecha_compra) as primera_compra,
                    MAX(t.fecha_compra) as ultima_compra
                FROM categorias c
                JOIN productos p ON c.id = p.categoria_id
                JOIN tickets t ON p.ticket_id = t.id
                GROUP BY c.id, c.nombre
                ORDER BY gasto_total DESC
            """)
            
            categories_data = cursor.fetchall()
            
            # Informe por subcategorías (top 20)
            cursor.execute("""
                SELECT 
                    c.nombre as categoria,
                    sc.nombre as subcategoria,
                    COUNT(p.id) as num_productos,
                    ROUND(SUM(p.precio_total), 2) as gasto_total,
                    ROUND(AVG(p.precio_total), 2) as precio_promedio
                FROM subcategorias sc
                JOIN categorias c ON sc.categoria_id = c.id
                JOIN productos p ON sc.id = p.subcategoria_id
                GROUP BY c.nombre, sc.nombre
                ORDER BY gasto_total DESC
                LIMIT 20
            """)
            
            subcategories_data = cursor.fetchall()
            cursor.close()
        
        # Generar informe
        report_lines = [
            "INFORME DE GASTOS POR CATEGORÍAS",
            "=" * 50,
            f"Generado: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "RESUMEN POR CATEGORÍAS:",
            "-" * 30
        ]
        
        total_general = 0
        for cat_data in categories_data:
            categoria, num_tickets, num_productos, cantidad, gasto, precio_prom, conf, primera, ultima = cat_data
            total_general += gasto
            
            report_lines.append(
                f"{categoria}:"
            )
            report_lines.append(
                f"  Tickets: {num_tickets} | Productos: {num_productos} | Gasto: {gasto:.2f}€"
            )
            report_lines.append(
                f"  Precio promedio: {precio_prom:.2f}€ | Confianza: {conf:.2f}"
            )
            report_lines.append("")
        
        report_lines.extend([
            f"TOTAL GENERAL: {total_general:.2f}€",
            "",
            "TOP 20 SUBCATEGORÍAS:",
            "-" * 25
        ])
        
        for subcat_data in subcategories_data:
            categoria, subcategoria, num_prod, gasto, precio_prom = subcat_data
            report_lines.append(
                f"{categoria} > {subcategoria}: {num_prod} productos - {gasto:.2f}€"
            )
        
        # Mostrar en consola
        report_text = "\n".join(report_lines)
        print(f"\n{report_text}")
        
        # Guardar en archivo si se especifica
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"📄 Informe guardado en: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generando informe: {e}")
        return False


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Categorizador de productos de tickets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python categorize_products.py                          # Categorizar productos nuevos
  python categorize_products.py --recategorize           # Recategorizar todos
  python categorize_products.py --stats                  # Ver estadísticas
  python categorize_products.py --report informe.txt     # Generar informe
  python categorize_products.py --batch-size 50          # Lotes de 50 productos
        """
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamaño del lote para procesamiento (default: 100)'
    )
    
    parser.add_argument(
        '--recategorize',
        action='store_true',
        help='Recategorizar todos los productos (limpiar existentes)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar estadísticas de categorización actual'
    )
    
    parser.add_argument(
        '--report',
        type=str,
        metavar='FILE',
        help='Generar informe de gastos por categorías'
    )
    
    args = parser.parse_args()
    
    # Modo estadísticas
    if args.stats:
        success = show_categorization_stats()
        sys.exit(0 if success else 1)
    
    # Modo informe
    if args.report:
        success = generate_category_report(args.report)
        sys.exit(0 if success else 1)
    
    # Modo categorización
    success = categorize_products(
        batch_size=args.batch_size,
        recategorize=args.recategorize
    )
    
    if success:
        # Mostrar estadísticas después de la categorización
        print("\n" + "="*60)
        show_categorization_stats()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()