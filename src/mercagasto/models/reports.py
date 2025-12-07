"""
Modelos para reportes de gastos.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ProductStats:
    """Estadísticas de un producto."""
    descripcion: str
    cantidad_total: int
    veces_comprado: int
    precio_promedio: float
    gasto_total: float


@dataclass
class DayStats:
    """Estadísticas de gastos por día."""
    dia: str
    total_gastado: float
    num_compras: int


@dataclass
class ComparisonStats:
    """Estadísticas de comparación entre períodos."""
    periodo_anterior: str
    total_anterior: float
    diferencia: float
    porcentaje: float


@dataclass
class WeeklyReport:
    """Reporte semanal de gastos."""
    periodo: str
    total: float
    num_tickets: int
    promedio_ticket: float
    top_productos: List[ProductStats]
    comparacion: ComparisonStats


@dataclass
class MonthlyReport:
    """Reporte mensual de gastos."""
    mes: str
    periodo: str
    total: float
    num_tickets: int
    promedio_ticket: float
    top_productos: List[ProductStats]
    gastos_por_dia: Dict[str, DayStats]
    comparacion: ComparisonStats