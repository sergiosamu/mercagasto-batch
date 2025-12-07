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
        if not self.invoice_number:
            raise ValueError("El número de factura es obligatorio")
        if not self.products:
            raise ValueError("El ticket debe tener al menos un producto")
        if self.total <= 0:
            raise ValueError("El total debe ser positivo")

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