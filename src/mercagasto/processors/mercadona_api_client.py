"""
Cliente para la API de Mercadona para obtener productos de categorías.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_logger
from ..models.enums import ProcessingStatus

logger = get_logger(__name__)


class MercadonaAPIClient:
    """Cliente para interactuar con la API de Mercadona."""
    
    BASE_URL = "https://tienda.mercadona.es/api"
    
    def __init__(self, lang: str = "es", timeout: int = 30, max_retries: int = 3):
        """
        Inicializa el cliente de la API de Mercadona.
        
        Args:
            lang: Idioma para las consultas (por defecto 'es')
            timeout: Timeout para las peticiones en segundos
            max_retries: Número máximo de reintentos
        """
        self.lang = lang
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
        
        logger.info(f"Cliente de API Mercadona inicializado (idioma: {lang})")
    
    def _create_session(self) -> requests.Session:
        """Crea una sesión HTTP con configuración de reintentos."""
        session = requests.Session()
        
        # Configurar estrategia de reintentos
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers por defecto
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': f'{self.lang},en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        return session
    
    def get_category_products(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los productos de una categoría específica.
        
        Args:
            category_id: ID de la categoría
            
        Returns:
            Diccionario con la información de la categoría y sus productos,
            o None si hay error
        """
        url = f"{self.BASE_URL}/categories/{category_id}/"
        params = {"lang": self.lang}
        
        try:
            logger.info(f"Obteniendo productos de categoría {category_id}")
            
            response = self.session.get(
                url, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Validar estructura básica
            if not isinstance(data, dict):
                logger.error(f"Respuesta inválida para categoría {category_id}")
                return None
            
            products_count = len(data.get('categories', []))
            logger.info(f"✓ Categoría {category_id}: {products_count} subcategorías encontradas")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión obteniendo categoría {category_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON para categoría {category_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado obteniendo categoría {category_id}: {e}")
            return None
    
    def get_subcategory_products(self, subcategory_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los productos de una subcategoría específica.
        
        Args:
            subcategory_id: ID de la subcategoría
            
        Returns:
            Diccionario con los productos de la subcategoría,
            o None si hay error
        """
        url = f"{self.BASE_URL}/categories/{subcategory_id}/"
        params = {"lang": self.lang}
        
        try:
            logger.debug(f"Obteniendo productos de subcategoría {subcategory_id}")
            
            response = self.session.get(
                url, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Validar estructura básica
            if not isinstance(data, dict):
                logger.error(f"Respuesta inválida para subcategoría {subcategory_id}")
                return None
            
            # Contar productos en todas las categorías anidadas
            products_count = 0
            categories = data.get('categories', [])
            for category in categories:
                products_count += len(category.get('products', []))
            
            logger.debug(f"Subcategoría {subcategory_id}: {products_count} productos encontrados")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión obteniendo subcategoría {subcategory_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON para subcategoría {subcategory_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado obteniendo subcategoría {subcategory_id}: {e}")
            return None
    
    def get_all_category_products(self, category_id: int, include_subcategories: bool = True) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Obtiene todos los productos de una categoría y sus subcategorías.
        
        Args:
            category_id: ID de la categoría principal
            include_subcategories: Si incluir productos de subcategorías
            
        Returns:
            Tupla con (info_categoria, lista_productos_todas_subcategorias)
        """
        # Obtener información de la categoría principal
        category_data = self.get_category_products(category_id)
        
        if not category_data:
            logger.error(f"No se pudo obtener información de categoría {category_id}")
            return {}, []
        
        all_products = []
        
        if include_subcategories:
            subcategories = category_data.get('categories', [])
            
            for subcategory in subcategories:
                subcategory_id = subcategory.get('id')
                
                if subcategory_id:
                    # Pequeña pausa para evitar sobrecargar la API
                    time.sleep(0.5)
                    
                    subcategory_data = self.get_subcategory_products(subcategory_id)
                    
                    if subcategory_data:
                        # Los productos están en subcategorías anidadas
                        nested_categories = subcategory_data.get('categories', [])
                        
                        for nested_cat in nested_categories:
                            products = nested_cat.get('products', [])
                            
                            # Añadir información de contexto a cada producto
                            for product in products:
                                product['category_id'] = category_id
                                product['category_name'] = category_data.get('name', '')
                                product['subcategory_id'] = subcategory_id
                                product['subcategory_name'] = subcategory.get('name', '')
                                product['nested_category_id'] = nested_cat.get('id')
                                product['nested_category_name'] = nested_cat.get('name', '')
                            
                            all_products.extend(products)
                        
                        total_products = sum(len(cat.get('products', [])) for cat in nested_categories)
                        logger.info(f"Subcategoría '{subcategory.get('name', 'Sin nombre')}' ({subcategory_id}): {total_products} productos")
        
        total_products = len(all_products)
        logger.info(f"✅ Categoría {category_id} completada: {total_products} productos totales")
        
        return category_data, all_products
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con la API de Mercadona.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            # Probar con una categoría conocida (agua y refrescos)
            test_category_id = 18
            result = self.get_category_products(test_category_id)
            
            if result:
                logger.info("✓ Conexión con API de Mercadona exitosa")
                return True
            else:
                logger.error("✗ Fallo en la conexión con API de Mercadona")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error probando conexión: {e}")
            return False
    
    def close(self):
        """Cierra la sesión HTTP."""
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("Sesión HTTP cerrada")


class MercadonaProductExtractor:
    """Extractor de información de productos de Mercadona."""
    
    def __init__(self, api_client: MercadonaAPIClient):
        """
        Inicializa el extractor.
        
        Args:
            api_client: Cliente de la API de Mercadona
        """
        self.api_client = api_client
        self.extracted_products = []
        self.extraction_stats = {
            'categories_processed': 0,
            'subcategories_processed': 0,
            'total_products': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def extract_product_info(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae información relevante de un producto.
        
        Args:
            product_data: Datos completos del producto de la API
            
        Returns:
            Diccionario con información simplificada del producto
        """
        try:
            price_instructions = product_data.get('price_instructions', {})
            
            return {
                'id': product_data.get('id'),
                'slug': product_data.get('slug', ''),
                'display_name': product_data.get('display_name', ''),
                'packaging': product_data.get('packaging', ''),
                'published': product_data.get('published', False),
                'share_url': product_data.get('share_url', ''),
                'thumbnail': product_data.get('thumbnail', ''),
                'limit': product_data.get('limit'),
                
                # Información de precios
                'unit_price': price_instructions.get('unit_price'),
                'bulk_price': price_instructions.get('bulk_price'),
                'reference_price': price_instructions.get('reference_price'),
                'previous_unit_price': price_instructions.get('previous_unit_price'),
                'price_decreased': price_instructions.get('price_decreased', False),
                'tax_percentage': price_instructions.get('tax_percentage'),
                'iva': price_instructions.get('iva'),
                'is_new': price_instructions.get('is_new', False),
                
                # Información de tamaño y empaque
                'unit_name': price_instructions.get('unit_name', ''),
                'unit_size': price_instructions.get('unit_size'),
                'size_format': price_instructions.get('size_format', ''),
                'reference_format': price_instructions.get('reference_format', ''),
                'is_pack': price_instructions.get('is_pack', False),
                'pack_size': price_instructions.get('pack_size'),
                'total_units': price_instructions.get('total_units'),
                'drained_weight': price_instructions.get('drained_weight'),
                
                # Selectores y métodos de venta
                'unit_selector': price_instructions.get('unit_selector', False),
                'bunch_selector': price_instructions.get('bunch_selector', False),
                'selling_method': price_instructions.get('selling_method'),
                'min_bunch_amount': price_instructions.get('min_bunch_amount'),
                'increment_bunch_amount': price_instructions.get('increment_bunch_amount'),
                'approx_size': price_instructions.get('approx_size', False),
                
                # Badges e información adicional
                'badges': product_data.get('badges', {}),
                'status': product_data.get('status'),
                'unavailable_from': product_data.get('unavailable_from'),
                'unavailable_weekdays': product_data.get('unavailable_weekdays', []),
                'categories': product_data.get('categories', []),
                
                # Información de contexto añadida por nuestro scraper
                'category_id': product_data.get('category_id'),
                'category_name': product_data.get('category_name', ''),
                'subcategory_id': product_data.get('subcategory_id'),
                'subcategory_name': product_data.get('subcategory_name', ''),
                'nested_category_id': product_data.get('nested_category_id'),
                'nested_category_name': product_data.get('nested_category_name', ''),
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error extrayendo información del producto {product_data.get('id', 'desconocido')}: {e}")
            return {}
    
    def extract_all_products(self, category_ids: List[int], delay_between_categories: float = 2.0) -> List[Dict[str, Any]]:
        """
        Extrae productos de múltiples categorías.
        
        Args:
            category_ids: Lista de IDs de categorías a procesar
            delay_between_categories: Pausa entre categorías en segundos
            
        Returns:
            Lista con todos los productos extraídos
        """
        self.extraction_stats['start_time'] = time.time()
        self.extracted_products = []
        
        logger.info(f"🚀 Iniciando extracción de {len(category_ids)} categorías")
        
        for i, category_id in enumerate(category_ids, 1):
            try:
                logger.info(f"📂 Procesando categoría {category_id} ({i}/{len(category_ids)})")
                
                # Obtener todos los productos de la categoría
                category_data, products = self.api_client.get_all_category_products(category_id)
                
                if not products:
                    logger.warning(f"No se encontraron productos en categoría {category_id}")
                    self.extraction_stats['errors'] += 1
                    continue
                
                # Procesar cada producto
                for product in products:
                    extracted_product = self.extract_product_info(product)
                    if extracted_product:
                        self.extracted_products.append(extracted_product)
                
                self.extraction_stats['categories_processed'] += 1
                self.extraction_stats['total_products'] += len(products)
                
                logger.info(f"✅ Categoría {category_id}: {len(products)} productos extraídos")
                
                # Pausa entre categorías para evitar sobrecargar la API
                if i < len(category_ids):
                    logger.debug(f"Pausa de {delay_between_categories}s antes de la siguiente categoría")
                    time.sleep(delay_between_categories)
                    
            except Exception as e:
                logger.error(f"Error procesando categoría {category_id}: {e}")
                self.extraction_stats['errors'] += 1
                continue
        
        self.extraction_stats['end_time'] = time.time()
        self._log_final_stats()
        
        return self.extracted_products
    
    def _log_final_stats(self):
        """Registra estadísticas finales de la extracción."""
        stats = self.extraction_stats
        duration = stats['end_time'] - stats['start_time']
        
        logger.info("🎯 EXTRACCIÓN COMPLETADA:")
        logger.info(f"   ⏱️  Duración: {duration:.2f} segundos")
        logger.info(f"   📂 Categorías procesadas: {stats['categories_processed']}")
        logger.info(f"   🛍️  Total productos: {stats['total_products']}")
        logger.info(f"   ❌ Errores: {stats['errors']}")
        
        if stats['total_products'] > 0:
            rate = stats['total_products'] / duration
            logger.info(f"   🚀 Velocidad: {rate:.2f} productos/segundo")
    
    def save_to_json(self, output_file: str) -> bool:
        """
        Guarda los productos extraídos en un archivo JSON.
        
        Args:
            output_file: Ruta del archivo de salida
            
        Returns:
            True si se guardó correctamente
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extraction_stats': self.extraction_stats,
                    'total_products': len(self.extracted_products),
                    'products': self.extracted_products
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Productos guardados en: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando productos en {output_file}: {e}")
            return False