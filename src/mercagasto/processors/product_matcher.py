"""
Módulo para matching de productos de tickets con categorías.

Este módulo implementa un sistema inteligente de matching que asocia
productos extraídos de tickets con categorías predefinidas usando
múltiples estrategias de coincidencia.
"""

import difflib
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import get_logger
from ..config.settings import DatabaseConfig

logger = get_logger(__name__)


@dataclass
class MatchResult:
    """Resultado de un matching de producto."""
    categoria_id: Optional[int]
    subcategoria_id: Optional[int]
    categoria_nombre: Optional[str] = None
    subcategoria_nombre: Optional[str] = None
    confidence: float = 0.0
    match_type: str = 'none'
    match_details: Optional[str] = None


class ProductMatcher:
    """
    Clase para matching inteligente de productos con categorías.
    
    Implementa múltiples estrategias de matching:
    1. Exact Match: Coincidencia exacta por nombre
    2. Fuzzy Match: Matching por similitud usando difflib
    3. Keyword Match: Búsqueda por palabras clave
    4. Price-based Match: Matching por precio cuando hay múltiples candidatos
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Inicializa el matcher de productos.
        
        Args:
            config: Configuración de la base de datos
        """
        self.connection_params = {
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'user': config.user,
            'password': config.password,
            'sslmode': config.sslmode,
            'connect_timeout': config.connect_timeout,
            'application_name': config.application_name
        }
        
        # Umbrales de confianza para matching
        self.EXACT_MATCH_THRESHOLD = 1.0
        self.FUZZY_MATCH_THRESHOLD = 0.8
        self.KEYWORD_MATCH_THRESHOLD = 0.6
        self.PRICE_MATCH_THRESHOLD = 0.7
        
        logger.info("ProductMatcher inicializado")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la BD."""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en conexión de BD: {e}")
            raise e
        finally:
            conn.close()
    
    def categorize_product(self, product_name: str, price: Optional[float] = None) -> MatchResult:
        """
        Categoriza un producto usando múltiples estrategias de matching.
        
        Args:
            product_name: Nombre del producto a categorizar
            price: Precio del producto (opcional)
        
        Returns:
            MatchResult con la mejor categorización encontrada
        """
        # Limpiar nombre del producto
        clean_name = self._clean_product_name(product_name)
        
        # Intentar matching exacto
        result = self._exact_match(clean_name)
        if result.confidence >= self.EXACT_MATCH_THRESHOLD:
            return result
        
        # Intentar fuzzy matching
        result = self._fuzzy_match(clean_name)
        if result.confidence >= self.FUZZY_MATCH_THRESHOLD:
            return result
        
        # Intentar keyword matching
        result = self._keyword_match(clean_name)
        if result.confidence >= self.KEYWORD_MATCH_THRESHOLD:
            return result
        
        # Intentar price matching si se proporciona precio
        if price is not None:
            result = self._price_match(clean_name, price)
            if result.confidence >= self.PRICE_MATCH_THRESHOLD:
                return result
        
        # Si no hay match, devolver resultado vacío
        logger.warning(f"No se pudo categorizar producto: {product_name}")
        return MatchResult(
            categoria_id=None,
            subcategoria_id=None,
            confidence=0.0,
            match_type='no_match',
            match_details=f"No se encontró categoría para: {product_name}"
        )
    
    def _clean_product_name(self, name: str) -> str:
        """Limpia el nombre del producto para mejorar el matching."""
        if not name:
            return ""
        
        # Convertir a minúsculas
        clean = name.lower().strip()
        
        # Remover caracteres especiales pero mantener espacios y números
        clean = re.sub(r'[^\w\s\d]', '', clean)
        
        # Normalizar espacios múltiples
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean
    
    def _exact_match(self, product_name: str) -> MatchResult:
        """Busca coincidencia exacta por nombre."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT DISTINCT
                            mp.categoria_id,
                            mp.subcategoria_id,
                            c.nombre as categoria_nombre,
                            s.nombre as subcategoria_nombre
                        FROM mercadona_productos mp
                        JOIN categorias c ON c.id = mp.categoria_id
                        LEFT JOIN subcategorias s ON s.id = mp.subcategoria_id
                        WHERE LOWER(TRIM(mp.display_name)) = %s
                        LIMIT 1
                    """, (product_name,))
                    
                    row = cursor.fetchone()
                    if row:
                        return MatchResult(
                            categoria_id=row['categoria_id'],
                            subcategoria_id=row['subcategoria_id'],
                            categoria_nombre=row['categoria_nombre'],
                            subcategoria_nombre=row['subcategoria_nombre'],
                            confidence=1.0,
                            match_type='exact',
                            match_details='Coincidencia exacta por nombre'
                        )
        
        except Exception as e:
            logger.error(f"Error en exact match: {e}")
        
        return MatchResult(categoria_id=None, subcategoria_id=None)
    
    def _fuzzy_match(self, product_name: str) -> MatchResult:
        """Busca coincidencias usando similitud de texto."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Obtener productos similares
                    cursor.execute("""
                        SELECT DISTINCT
                            mp.display_name,
                            mp.categoria_id,
                            mp.subcategoria_id,
                            c.nombre as categoria_nombre,
                            s.nombre as subcategoria_nombre
                        FROM mercadona_productos mp
                        JOIN categorias c ON c.id = mp.categoria_id
                        LEFT JOIN subcategorias s ON s.id = mp.subcategoria_id
                        WHERE mp.display_name IS NOT NULL
                    """)
                    
                    best_match = None
                    best_ratio = 0.0
                    
                    for row in cursor.fetchall():
                        clean_catalog_name = self._clean_product_name(row['display_name'])
                        ratio = difflib.SequenceMatcher(None, product_name, clean_catalog_name).ratio()
                        
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = row
                    
                    if best_match and best_ratio >= 0.8:  # Umbral mínimo para fuzzy
                        return MatchResult(
                            categoria_id=best_match['categoria_id'],
                            subcategoria_id=best_match['subcategoria_id'],
                            categoria_nombre=best_match['categoria_nombre'],
                            subcategoria_nombre=best_match['subcategoria_nombre'],
                            confidence=best_ratio,
                            match_type='fuzzy',
                            match_details=f'Similitud {best_ratio:.2f} con "{best_match["display_name"]}"'
                        )
        
        except Exception as e:
            logger.error(f"Error en fuzzy match: {e}")
        
        return MatchResult(categoria_id=None, subcategoria_id=None)
    
    def _keyword_match(self, product_name: str) -> MatchResult:
        """Busca coincidencias por palabras clave."""
        try:
            words = product_name.split()
            if not words:
                return MatchResult(categoria_id=None, subcategoria_id=None)
            
            # Buscar por cada palabra significativa (>3 caracteres)
            significant_words = [w for w in words if len(w) > 3]
            
            if not significant_words:
                return MatchResult(categoria_id=None, subcategoria_id=None)
            
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Crear condiciones de búsqueda
                    conditions = []
                    params = []
                    
                    for word in significant_words:
                        conditions.append("LOWER(mp.display_name) LIKE %s")
                        params.append(f"%{word}%")
                    
                    query = f"""
                        SELECT 
                            mp.categoria_id,
                            mp.subcategoria_id,
                            c.nombre as categoria_nombre,
                            s.nombre as subcategoria_nombre,
                            mp.display_name,
                            COUNT(*) as matches
                        FROM mercadona_productos mp
                        JOIN categorias c ON c.id = mp.categoria_id
                        LEFT JOIN subcategorias s ON s.id = mp.subcategoria_id
                        WHERE ({' OR '.join(conditions)})
                        GROUP BY mp.categoria_id, mp.subcategoria_id, c.nombre, s.nombre, mp.display_name
                        ORDER BY matches DESC, mp.categoria_id
                        LIMIT 1
                    """
                    
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    
                    if row:
                        # Calcular confianza basada en número de palabras coincidentes
                        confidence = min(0.9, row['matches'] / len(significant_words))
                        
                        return MatchResult(
                            categoria_id=row['categoria_id'],
                            subcategoria_id=row['subcategoria_id'],
                            categoria_nombre=row['categoria_nombre'],
                            subcategoria_nombre=row['subcategoria_nombre'],
                            confidence=confidence,
                            match_type='keyword',
                            match_details=f'Coincidencia por palabras clave: {row["matches"]} de {len(significant_words)}'
                        )
        
        except Exception as e:
            logger.error(f"Error en keyword match: {e}")
        
        return MatchResult(categoria_id=None, subcategoria_id=None)
    
    def _price_match(self, product_name: str, price: float) -> MatchResult:
        """Busca coincidencias considerando precio."""
        try:
            # Buscar productos con precio similar (+/- 20%)
            price_margin = 0.2
            min_price = price * (1 - price_margin)
            max_price = price * (1 + price_margin)
            
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            mp.categoria_id,
                            mp.subcategoria_id,
                            c.nombre as categoria_nombre,
                            s.nombre as subcategoria_nombre,
                            mp.display_name,
                            mp.unit_price,
                            ABS(mp.unit_price - %s) as price_diff
                        FROM mercadona_productos mp
                        JOIN categorias c ON c.id = mp.categoria_id
                        LEFT JOIN subcategorias s ON s.id = mp.subcategoria_id
                        WHERE mp.unit_price IS NOT NULL 
                        AND mp.unit_price BETWEEN %s AND %s
                        ORDER BY price_diff
                        LIMIT 1
                    """, (price, min_price, max_price))
                    
                    row = cursor.fetchone()
                    if row:
                        # Calcular confianza basada en proximidad del precio
                        price_diff = float(row['price_diff'])
                        unit_price = float(row['unit_price'])
                        price_similarity = 1 - (price_diff / price)
                        confidence = max(0.5, price_similarity)  # Mínimo 0.5 para price match
                        
                        return MatchResult(
                            categoria_id=row['categoria_id'],
                            subcategoria_id=row['subcategoria_id'],
                            categoria_nombre=row['categoria_nombre'],
                            subcategoria_nombre=row['subcategoria_nombre'],
                            confidence=confidence,
                            match_type='price',
                            match_details=f'Coincidencia por precio: €{unit_price:.2f} vs €{price:.2f}'
                        )
        
        except Exception as e:
            logger.error(f"Error en price match: {e}")
        
        return MatchResult(categoria_id=None, subcategoria_id=None)
    
    def update_product_category(self, product_id: int, match_result: MatchResult) -> bool:
        """
        Actualiza la categoría de un producto en la base de datos.
        
        Args:
            product_id: ID del producto a actualizar
            match_result: Resultado del matching
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE productos 
                        SET 
                            categoria_id = %s,
                            subcategoria_id = %s,
                            categoria_detectada = %s,
                            subcategoria_detectada = %s,
                            confidence_score = %s,
                            matching_method = %s
                        WHERE id = %s
                    """, (
                        match_result.categoria_id,
                        match_result.subcategoria_id,
                        match_result.categoria_nombre,
                        match_result.subcategoria_nombre,
                        match_result.confidence,
                        match_result.match_type,
                        product_id
                    ))
                    
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Producto {product_id} categorizado: {match_result.categoria_nombre or 'Sin categoría'}")
                        return True
                    else:
                        logger.warning(f"No se encontró producto con ID {product_id}")
                        return False
        
        except Exception as e:
            logger.error(f"Error actualizando categoría de producto {product_id}: {e}")
            return False
    
    def categorize_uncategorized_products(self) -> Dict[str, int]:
        """
        Categoriza todos los productos sin categoría.
        
        Returns:
            Diccionario con estadísticas de categorización
        """
        stats = {
            'processed': 0,
            'categorized': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Obtener productos sin categoría
                    cursor.execute("""
                        SELECT id, descripcion, precio_unitario
                        FROM productos 
                        WHERE categoria_id IS NULL
                        ORDER BY id
                    """)
                    
                    products = cursor.fetchall()
                    stats['processed'] = len(products)
                    
                    logger.info(f"Categorizando {len(products)} productos sin categoría")
                    
                    for product in products:
                        try:
                            match_result = self.categorize_product(
                                product['descripcion'], 
                                product['precio_unitario']
                            )
                            
                            if match_result.categoria_id:
                                if self.update_product_category(product['id'], match_result):
                                    stats['categorized'] += 1
                                else:
                                    stats['failed'] += 1
                            else:
                                stats['skipped'] += 1
                                
                        except Exception as e:
                            logger.error(f"Error categorizando producto {product['id']}: {e}")
                            stats['failed'] += 1
            
            logger.info(f"Categorización completada: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error en categorización masiva: {e}")
            return stats
    
    def get_categorization_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de categorización.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Estadísticas generales
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_products,
                            COUNT(categoria_id) as categorized,
                            COUNT(*) - COUNT(categoria_id) as uncategorized,
                            AVG(match_confidence) as avg_confidence,
                            COUNT(CASE WHEN match_confidence >= 0.8 THEN 1 END) as high_confidence,
                            COUNT(CASE WHEN match_confidence BETWEEN 0.6 AND 0.8 THEN 1 END) as medium_confidence,
                            COUNT(CASE WHEN match_confidence < 0.6 THEN 1 END) as low_confidence
                        FROM productos
                    """)
                    
                    general_stats = cursor.fetchone()
                    
                    # Estadísticas por tipo de match
                    cursor.execute("""
                        SELECT 
                            match_type,
                            COUNT(*) as count,
                            AVG(match_confidence) as avg_confidence
                        FROM productos 
                        WHERE match_type IS NOT NULL
                        GROUP BY match_type
                        ORDER BY count DESC
                    """)
                    
                    match_type_stats = cursor.fetchall()
                    
                    # Categorías más populares
                    cursor.execute("""
                        SELECT 
                            c.nombre as categoria,
                            COUNT(*) as productos
                        FROM productos p
                        JOIN categorias c ON c.id = p.categoria_id
                        GROUP BY c.nombre
                        ORDER BY productos DESC
                        LIMIT 10
                    """)
                    
                    top_categories = cursor.fetchall()
                    
                    return {
                        'general': dict(general_stats),
                        'by_match_type': [dict(row) for row in match_type_stats],
                        'top_categories': [dict(row) for row in top_categories]
                    }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}