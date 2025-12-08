"""
Modelos de datos principales del sistema.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class ProcessingError:
    """Información de un error de procesamiento."""
    timestamp: datetime
    stage: str
    error_type: str
    error_message: str
    traceback: str
    recoverable: bool


@dataclass
class Product:
    """Representa un producto en el ticket."""
    quantity: int
    description: str
    unit_price: Optional[float]
    total_price: float
    weight: Optional[str] = None

    def __post_init__(self):
        """Validaciones post-inicialización."""
        if self.quantity <= 0:
            raise ValueError("La cantidad debe ser positiva")
        if self.total_price <= 0:
            raise ValueError("El precio total debe ser positivo")
        if not self.description or not self.description.strip():
            raise ValueError("La descripción no puede estar vacía")


@dataclass
class TicketData:
    """Representa todos los datos del ticket."""
    store_name: str
    cif: str
    address: str
    postal_code: str
    city: str
    phone: str
    date: datetime
    time: str
    order_number: str
    invoice_number: str
    products: List[Product]
    total: float
    payment_method: str
    iva_breakdown: Dict[str, Dict[str, float]]

    def __post_init__(self):
        """Validaciones post-inicialización."""
        # Permitir crear tickets sin productos para debugging
        # Solo validar si hay al menos algunos datos críticos
        if self.total <= 0 and self.products:
            raise ValueError("El total debe ser positivo cuando hay productos")
        
        # Validaciones solo para datos que realmente están presentes
        if self.store_name and not self.store_name.strip():
            raise ValueError("El nombre de la tienda no puede estar vacío")
        if self.cif and not self.cif.strip():
            raise ValueError("El CIF no puede estar vacío")
    
    def validate_for_storage(self):
        """Validación estricta antes de guardar en base de datos."""
        if not self.products:
            raise ValueError("El ticket debe tener al menos un producto para almacenar")
        if self.total <= 0:
            raise ValueError("El total debe ser positivo para almacenar")
        if not self.store_name or not self.store_name.strip():
            raise ValueError("El nombre de la tienda es obligatorio para almacenar")
        if not self.cif or not self.cif.strip():
            raise ValueError("El CIF es obligatorio para almacenar")
        if not self.date:
            raise ValueError("La fecha es obligatoria para almacenar")
        if not self.invoice_number or not self.invoice_number.strip():
            raise ValueError("El número de factura es obligatorio para almacenar")

    @property
    def products_total(self) -> float:
        """Calcula la suma total de los productos."""
        return sum(product.total_price for product in self.products)

    @property
    def is_total_consistent(self) -> bool:
        """Verifica si el total coincide con la suma de productos."""
        return abs(self.products_total - self.total) <= 0.5  # Tolerancia de 0.5€

    def get_product_count(self) -> int:
        """Obtiene el número total de productos."""
        return len(self.products)

    def get_total_quantity(self) -> int:
        """Obtiene la cantidad total de todos los productos."""
        return sum(product.quantity for product in self.products)