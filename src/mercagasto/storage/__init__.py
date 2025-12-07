"""
Módulo de almacenamiento y persistencia.
"""

from .base import TicketStorageBase
from .postgresql import PostgreSQLTicketStorage
from .product_loader import MercadonaProductLoader

__all__ = [
    'TicketStorageBase',
    'PostgreSQLTicketStorage',
    'MercadonaProductLoader'
]