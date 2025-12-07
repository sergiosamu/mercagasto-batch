"""
Cargador de productos de Mercadona en la base de datos.
"""

import json
import psycopg2
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..config import get_logger, DatabaseConfig
from .base import TicketStorageBase

logger = get_logger(__name__)


class MercadonaProductLoader:
    """Cargador de productos de Mercadona en PostgreSQL."""
    
    def __init__(self, db_config: DatabaseConfig):
        """
        Inicializa el cargador de productos.
        
        Args:
            db_config: Configuración de la base de datos
        """
        self.db_config = db_config
        self.connection = None
        
    def connect(self):
        """Establece conexión con la base de datos."""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            logger.info("✓ Conectado a la base de datos para carga de productos")
            
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        if self.connection:
            self.connection.close()
            logger.info("Conexión cerrada")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Convierte un valor a Decimal de forma segura."""
        if value is None or value == '' or value == 'N/A':
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Convierte un valor a int de forma segura."""
        if value is None or value == '' or value == 'N/A':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_bool(self, value: Any) -> bool:
        """Convierte un valor a bool de forma segura."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def _prepare_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara los datos del producto para inserción en la base de datos.
        
        Args:
            product: Datos del producto desde JSON
            
        Returns:
            Diccionario con datos preparados para PostgreSQL
        """
        # Convertir string de fecha a timestamp si es necesario
        extraction_date = product.get('extraction_date')
        if isinstance(extraction_date, str):
            try:
                extraction_date = datetime.strptime(extraction_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                extraction_date = datetime.now()
        elif not extraction_date:
            extraction_date = datetime.now()
        
        return {
            'id': str(product.get('id', '')),
            'slug': product.get('slug', '')[:200],
            'display_name': product.get('display_name', '')[:300],
            'packaging': product.get('packaging', '')[:100] if product.get('packaging') else None,
            'published': self._safe_bool(product.get('published', True)),
            'share_url': product.get('share_url'),
            'thumbnail': product.get('thumbnail'),
            'product_limit': self._safe_int(product.get('limit')),
            
            # Precios
            'unit_price': self._safe_decimal(product.get('unit_price')),
            'bulk_price': self._safe_decimal(product.get('bulk_price')),
            'reference_price': self._safe_decimal(product.get('reference_price')),
            'previous_unit_price': self._safe_decimal(product.get('previous_unit_price')),
            'price_decreased': self._safe_bool(product.get('price_decreased', False)),
            'tax_percentage': self._safe_decimal(product.get('tax_percentage')),
            'iva': self._safe_int(product.get('iva')),
            'is_new': self._safe_bool(product.get('is_new', False)),
            
            # Tamaños y empaque
            'unit_name': product.get('unit_name', '')[:50] if product.get('unit_name') else None,
            'unit_size': self._safe_decimal(product.get('unit_size')),
            'size_format': product.get('size_format', '')[:20] if product.get('size_format') else None,
            'reference_format': product.get('reference_format', '')[:20] if product.get('reference_format') else None,
            'is_pack': self._safe_bool(product.get('is_pack', False)),
            'pack_size': self._safe_decimal(product.get('pack_size')),
            'total_units': self._safe_int(product.get('total_units')),
            'drained_weight': self._safe_decimal(product.get('drained_weight')),
            
            # Selectores
            'unit_selector': self._safe_bool(product.get('unit_selector', False)),
            'bunch_selector': self._safe_bool(product.get('bunch_selector', False)),
            'selling_method': self._safe_int(product.get('selling_method')),
            'min_bunch_amount': self._safe_decimal(product.get('min_bunch_amount')),
            'increment_bunch_amount': self._safe_decimal(product.get('increment_bunch_amount')),
            'approx_size': self._safe_bool(product.get('approx_size', False)),
            
            # JSON fields
            'badges': json.dumps(product.get('badges', {})) if product.get('badges') else None,
            'status': product.get('status'),
            'unavailable_from': None,  # TODO: parsear si viene como string
            'unavailable_weekdays': json.dumps(product.get('unavailable_weekdays', [])),
            'api_categories': json.dumps(product.get('categories', [])),
            
            # Contexto
            'categoria_id': self._safe_int(product.get('category_id')),
            'categoria_name': product.get('category_name', '')[:100] if product.get('category_name') else None,
            'subcategoria_id': self._safe_int(product.get('subcategory_id')),
            'subcategoria_name': product.get('subcategory_name', '')[:100] if product.get('subcategory_name') else None,
            'nested_category_id': self._safe_int(product.get('nested_category_id')),
            'nested_category_name': product.get('nested_category_name', '')[:100] if product.get('nested_category_name') else None,
            
            # Metadatos
            'extraction_date': extraction_date
        }
    
    def insert_product(self, product: Dict[str, Any]) -> bool:
        """
        Inserta un producto en la base de datos.
        
        Args:
            product: Datos del producto
            
        Returns:
            True si se insertó correctamente
        """
        if not self.connection:
            raise RuntimeError("No hay conexión a la base de datos")
        
        try:
            prepared_data = self._prepare_product_data(product)
            
            # Validar datos mínimos requeridos
            if not prepared_data['id'] or not prepared_data['display_name']:
                logger.warning(f"Producto con datos insuficientes: {prepared_data.get('id', 'sin ID')}")
                return False
            
            cursor = self.connection.cursor()
            
            # INSERT con ON CONFLICT para manejar duplicados
            insert_sql = """
                INSERT INTO mercadona_productos (
                    id, slug, display_name, packaging, published, share_url, thumbnail, product_limit,
                    unit_price, bulk_price, reference_price, previous_unit_price, price_decreased, 
                    tax_percentage, iva, is_new,
                    unit_name, unit_size, size_format, reference_format, is_pack, pack_size, 
                    total_units, drained_weight,
                    unit_selector, bunch_selector, selling_method, min_bunch_amount, 
                    increment_bunch_amount, approx_size,
                    badges, status, unavailable_from, unavailable_weekdays, api_categories,
                    categoria_id, categoria_name, subcategoria_id, subcategoria_name,
                    nested_category_id, nested_category_name, extraction_date
                ) VALUES (
                    %(id)s, %(slug)s, %(display_name)s, %(packaging)s, %(published)s, %(share_url)s, 
                    %(thumbnail)s, %(product_limit)s,
                    %(unit_price)s, %(bulk_price)s, %(reference_price)s, %(previous_unit_price)s, 
                    %(price_decreased)s, %(tax_percentage)s, %(iva)s, %(is_new)s,
                    %(unit_name)s, %(unit_size)s, %(size_format)s, %(reference_format)s, %(is_pack)s, 
                    %(pack_size)s, %(total_units)s, %(drained_weight)s,
                    %(unit_selector)s, %(bunch_selector)s, %(selling_method)s, %(min_bunch_amount)s, 
                    %(increment_bunch_amount)s, %(approx_size)s,
                    %(badges)s, %(status)s, %(unavailable_from)s, %(unavailable_weekdays)s, 
                    %(api_categories)s,
                    %(categoria_id)s, %(categoria_name)s, %(subcategoria_id)s, %(subcategoria_name)s,
                    %(nested_category_id)s, %(nested_category_name)s, %(extraction_date)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    slug = EXCLUDED.slug,
                    display_name = EXCLUDED.display_name,
                    packaging = EXCLUDED.packaging,
                    published = EXCLUDED.published,
                    share_url = EXCLUDED.share_url,
                    thumbnail = EXCLUDED.thumbnail,
                    product_limit = EXCLUDED.product_limit,
                    unit_price = EXCLUDED.unit_price,
                    bulk_price = EXCLUDED.bulk_price,
                    reference_price = EXCLUDED.reference_price,
                    previous_unit_price = EXCLUDED.previous_unit_price,
                    price_decreased = EXCLUDED.price_decreased,
                    tax_percentage = EXCLUDED.tax_percentage,
                    iva = EXCLUDED.iva,
                    is_new = EXCLUDED.is_new,
                    unit_name = EXCLUDED.unit_name,
                    unit_size = EXCLUDED.unit_size,
                    size_format = EXCLUDED.size_format,
                    reference_format = EXCLUDED.reference_format,
                    is_pack = EXCLUDED.is_pack,
                    pack_size = EXCLUDED.pack_size,
                    total_units = EXCLUDED.total_units,
                    drained_weight = EXCLUDED.drained_weight,
                    unit_selector = EXCLUDED.unit_selector,
                    bunch_selector = EXCLUDED.bunch_selector,
                    selling_method = EXCLUDED.selling_method,
                    min_bunch_amount = EXCLUDED.min_bunch_amount,
                    increment_bunch_amount = EXCLUDED.increment_bunch_amount,
                    approx_size = EXCLUDED.approx_size,
                    badges = EXCLUDED.badges,
                    status = EXCLUDED.status,
                    unavailable_from = EXCLUDED.unavailable_from,
                    unavailable_weekdays = EXCLUDED.unavailable_weekdays,
                    api_categories = EXCLUDED.api_categories,
                    categoria_id = EXCLUDED.categoria_id,
                    categoria_name = EXCLUDED.categoria_name,
                    subcategoria_id = EXCLUDED.subcategoria_id,
                    subcategoria_name = EXCLUDED.subcategoria_name,
                    nested_category_id = EXCLUDED.nested_category_id,
                    nested_category_name = EXCLUDED.nested_category_name,
                    extraction_date = EXCLUDED.extraction_date,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_sql, prepared_data)
            cursor.close()
            
            logger.debug(f"Producto {prepared_data['id']} insertado/actualizado")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando producto {product.get('id', 'desconocido')}: {e}")
            return False
    
    def load_products_from_json(self, json_file: str, batch_size: int = 100) -> Dict[str, int]:
        """
        Carga productos desde un archivo JSON.
        
        Args:
            json_file: Ruta al archivo JSON con productos
            batch_size: Tamaño del lote para commits
            
        Returns:
            Diccionario con estadísticas de la carga
        """
        stats = {
            'total_products': 0,
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        logger.info(f"🚀 Iniciando carga de productos desde {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', [])
            stats['total_products'] = len(products)
            
            if not products:
                logger.warning("No se encontraron productos en el archivo JSON")
                return stats
            
            logger.info(f"📦 {len(products)} productos encontrados en el archivo")
            
            # Procesar en lotes
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(products) + batch_size - 1) // batch_size
                
                logger.info(f"📊 Procesando lote {batch_num}/{total_batches} ({len(batch)} productos)")
                
                for product in batch:
                    try:
                        # Verificar si el producto ya existe
                        cursor = self.connection.cursor()
                        cursor.execute(
                            "SELECT id FROM mercadona_productos WHERE id = %s",
                            (str(product.get('id', '')),)
                        )
                        exists = cursor.fetchone()
                        cursor.close()
                        
                        # Insertar/actualizar producto
                        if self.insert_product(product):
                            if exists:
                                stats['updated'] += 1
                            else:
                                stats['inserted'] += 1
                        else:
                            stats['skipped'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error procesando producto {product.get('id', 'desconocido')}: {e}")
                        stats['errors'] += 1
                
                # Commit del lote
                self.connection.commit()
                logger.debug(f"Lote {batch_num} committed")
            
            # Estadísticas finales
            logger.info("🎯 CARGA COMPLETADA:")
            logger.info(f"   📦 Total productos: {stats['total_products']}")
            logger.info(f"   ✅ Insertados: {stats['inserted']}")
            logger.info(f"   🔄 Actualizados: {stats['updated']}")
            logger.info(f"   ⚠️  Omitidos: {stats['skipped']}")
            logger.info(f"   ❌ Errores: {stats['errors']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error cargando productos desde JSON: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def clear_old_products(self, days_old: int = 7) -> int:
        """
        Elimina productos antiguos de la base de datos.
        
        Args:
            days_old: Días de antigüedad para considerar productos obsoletos
            
        Returns:
            Número de productos eliminados
        """
        if not self.connection:
            raise RuntimeError("No hay conexión a la base de datos")
        
        try:
            cursor = self.connection.cursor()
            
            delete_sql = """
                DELETE FROM mercadona_productos 
                WHERE extraction_date < CURRENT_DATE - INTERVAL '%s days'
            """
            
            cursor.execute(delete_sql, (days_old,))
            deleted_count = cursor.rowcount
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"🗑️  Eliminados {deleted_count} productos antiguos (>{days_old} días)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error eliminando productos antiguos: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def get_products_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de los productos en la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.connection:
            raise RuntimeError("No hay conexión a la base de datos")
        
        try:
            cursor = self.connection.cursor()
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN published = true THEN 1 END) as publicados,
                    COUNT(CASE WHEN price_decreased = true THEN 1 END) as en_oferta,
                    COUNT(DISTINCT categoria_id) as categorias,
                    COUNT(DISTINCT subcategoria_id) as subcategorias,
                    MIN(extraction_date) as primera_extraccion,
                    MAX(extraction_date) as ultima_extraccion
                FROM mercadona_productos
            """)
            
            row = cursor.fetchone()
            summary = {
                'total_productos': row[0],
                'productos_publicados': row[1],
                'productos_en_oferta': row[2],
                'total_categorias': row[3],
                'total_subcategorias': row[4],
                'primera_extraccion': row[5],
                'ultima_extraccion': row[6]
            }
            
            # Top categorías
            cursor.execute("""
                SELECT categoria_name, COUNT(*) as count
                FROM mercadona_productos
                WHERE categoria_name IS NOT NULL
                GROUP BY categoria_name
                ORDER BY count DESC
                LIMIT 5
            """)
            
            summary['top_categorias'] = [
                {'categoria': row[0], 'productos': row[1]}
                for row in cursor.fetchall()
            ]
            
            cursor.close()
            return summary
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de productos: {e}")
            raise