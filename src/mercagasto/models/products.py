"""
Modelos de datos para productos de Mercadona.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ProductInfo:
    """Información de un producto de Mercadona."""
    id: int
    display_name: str
    slug: str
    brand: str
    unit_price: Optional[float]
    unit_name: str
    unit_size: Optional[float]
    bulk_price: Optional[float]
    approx_size: Optional[str]
    size_format: str
    total_units: Optional[int]
    unit_selector: bool
    bunch_selector: bool
    drained_weight: Optional[float]
    selling_method: Optional[int]
    price_decreased: bool
    reference_format: str
    reference_price: Optional[float]
    increment_bunch_amount: Optional[float]
    published: bool
    share_url: str
    thumbnail: str
    category_id: Optional[int]
    category_name: str
    subcategory_id: Optional[int]
    subcategory_name: str
    extraction_date: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductInfo':
        """Crea una instancia desde un diccionario."""
        return cls(
            id=data.get('id', 0),
            display_name=data.get('display_name', ''),
            slug=data.get('slug', ''),
            brand=data.get('brand', ''),
            unit_price=data.get('unit_price'),
            unit_name=data.get('unit_name', ''),
            unit_size=data.get('unit_size'),
            bulk_price=data.get('bulk_price'),
            approx_size=data.get('approx_size'),
            size_format=data.get('size_format', ''),
            total_units=data.get('total_units'),
            unit_selector=data.get('unit_selector', False),
            bunch_selector=data.get('bunch_selector', False),
            drained_weight=data.get('drained_weight'),
            selling_method=data.get('selling_method'),
            price_decreased=data.get('price_decreased', False),
            reference_format=data.get('reference_format', ''),
            reference_price=data.get('reference_price'),
            increment_bunch_amount=data.get('increment_bunch_amount'),
            published=data.get('published', False),
            share_url=data.get('share_url', ''),
            thumbnail=data.get('thumbnail', ''),
            category_id=data.get('category_id'),
            category_name=data.get('category_name', ''),
            subcategory_id=data.get('subcategory_id'),
            subcategory_name=data.get('subcategory_name', ''),
            extraction_date=data.get('extraction_date', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia a diccionario."""
        return {
            'id': self.id,
            'display_name': self.display_name,
            'slug': self.slug,
            'brand': self.brand,
            'unit_price': self.unit_price,
            'unit_name': self.unit_name,
            'unit_size': self.unit_size,
            'bulk_price': self.bulk_price,
            'approx_size': self.approx_size,
            'size_format': self.size_format,
            'total_units': self.total_units,
            'unit_selector': self.unit_selector,
            'bunch_selector': self.bunch_selector,
            'drained_weight': self.drained_weight,
            'selling_method': self.selling_method,
            'price_decreased': self.price_decreased,
            'reference_format': self.reference_format,
            'reference_price': self.reference_price,
            'increment_bunch_amount': self.increment_bunch_amount,
            'published': self.published,
            'share_url': self.share_url,
            'thumbnail': self.thumbnail,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'subcategory_id': self.subcategory_id,
            'subcategory_name': self.subcategory_name,
            'extraction_date': self.extraction_date
        }


@dataclass
class CategoryInfo:
    """Información de una categoría de Mercadona."""
    id: int
    name: str
    order: int
    is_extended: bool
    subcategories: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryInfo':
        """Crea una instancia desde un diccionario."""
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            order=data.get('order', 0),
            is_extended=data.get('is_extended', False),
            subcategories=data.get('categories', [])
        )


@dataclass
class ProductExtractionStats:
    """Estadísticas de una extracción de productos."""
    categories_processed: int
    subcategories_processed: int
    total_products: int
    errors: int
    start_time: Optional[float]
    end_time: Optional[float]
    
    @property
    def duration(self) -> float:
        """Duración de la extracción en segundos."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def products_per_second(self) -> float:
        """Productos procesados por segundo."""
        duration = self.duration
        if duration > 0:
            return self.total_products / duration
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'categories_processed': self.categories_processed,
            'subcategories_processed': self.subcategories_processed,
            'total_products': self.total_products,
            'errors': self.errors,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'products_per_second': self.products_per_second
        }