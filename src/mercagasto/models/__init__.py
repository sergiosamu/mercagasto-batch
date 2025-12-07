"""
Modelos de datos del sistema.
"""

from .enums import ProcessingStatus
from .ticket import ProcessingError, Product, TicketData
from .products import ProductInfo, CategoryInfo, ProductExtractionStats
from .reports import (
    ProductStats, DayStats, ComparisonStats, 
    WeeklyReport, MonthlyReport
)

__all__ = [
    'ProcessingStatus',
    'ProcessingError',
    'Product',
    'TicketData',
    'ProductInfo',
    'CategoryInfo',
    'ProductExtractionStats',
    'ProductStats',
    'DayStats', 
    'ComparisonStats',
    'WeeklyReport',
    'MonthlyReport'
]