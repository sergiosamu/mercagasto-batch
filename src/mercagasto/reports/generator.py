"""
Generador de reportes de gastos.
"""

import calendar
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..models import WeeklyReport, MonthlyReport, ProductStats, ComparisonStats, DayStats
from ..storage import TicketStorageBase
from ..config import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generador de reportes de gastos."""
    
    def __init__(self, storage: TicketStorageBase):
        """
        Inicializa el generador de reportes.
        
        Args:
            storage: Instancia de almacenamiento de tickets
        """
        self.storage = storage
    
    def generate_weekly_report(self) -> WeeklyReport:
        """Genera reporte semanal de gastos."""
        logger.info("Generando reporte semanal...")
        
        hoy = datetime.now()
        hace_7_dias = hoy - timedelta(days=7)
        
        # Obtener datos de la semana actual
        total_semana = self.storage.get_total_gastado(
            hace_7_dias.strftime('%Y-%m-%d'),
            hoy.strftime('%Y-%m-%d')
        )
        
        tickets_semana = self.storage.get_tickets_by_date_range(
            hace_7_dias.strftime('%Y-%m-%d'),
            hoy.strftime('%Y-%m-%d')
        )
        
        # Top productos de la semana
        top_productos = self._get_top_productos_periodo(hace_7_dias.date(), hoy.date(), limit=5)
        
        # Comparar con semana anterior
        hace_14_dias = hoy - timedelta(days=14)
        total_semana_anterior = self.storage.get_total_gastado(
            hace_14_dias.strftime('%Y-%m-%d'),
            hace_7_dias.strftime('%Y-%m-%d')
        )
        
        comparacion = self._calculate_comparison(
            total_semana_anterior, total_semana, "semana anterior"
        )
        
        return WeeklyReport(
            periodo=f"{hace_7_dias.strftime('%d/%m/%Y')} - {hoy.strftime('%d/%m/%Y')}",
            total=total_semana,
            num_tickets=len(tickets_semana),
            promedio_ticket=total_semana / len(tickets_semana) if tickets_semana else 0,
            top_productos=top_productos,
            comparacion=comparacion
        )
    
    def generate_monthly_report(self) -> MonthlyReport:
        """Genera reporte mensual de gastos."""
        logger.info("Generando reporte mensual...")
        
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1)
        
        # Último día del mes
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fin_mes = hoy.replace(day=ultimo_dia)
        
        # Obtener datos del mes actual
        total_mes = self.storage.get_total_gastado(
            inicio_mes.strftime('%Y-%m-%d'),
            fin_mes.strftime('%Y-%m-%d')
        )
        
        tickets_mes = self.storage.get_tickets_by_date_range(
            inicio_mes.strftime('%Y-%m-%d'),
            fin_mes.strftime('%Y-%m-%d')
        )
        
        # Top productos del mes
        top_productos = self._get_top_productos_periodo(inicio_mes.date(), fin_mes.date(), limit=10)
        
        # Gastos por día de la semana
        gastos_por_dia = self._get_gastos_por_dia_semana(inicio_mes.date(), fin_mes.date())
        
        # Comparar con mes anterior
        if hoy.month == 1:
            mes_anterior = hoy.replace(year=hoy.year-1, month=12, day=1)
        else:
            mes_anterior = hoy.replace(month=hoy.month-1, day=1)
        
        ultimo_dia_anterior = calendar.monthrange(mes_anterior.year, mes_anterior.month)[1]
        fin_mes_anterior = mes_anterior.replace(day=ultimo_dia_anterior)
        
        total_mes_anterior = self.storage.get_total_gastado(
            mes_anterior.strftime('%Y-%m-%d'),
            fin_mes_anterior.strftime('%Y-%m-%d')
        )
        
        comparacion = self._calculate_comparison(
            total_mes_anterior, total_mes, mes_anterior.strftime('%B')
        )
        
        return MonthlyReport(
            mes=hoy.strftime('%B %Y'),
            periodo=f"{inicio_mes.strftime('%d/%m/%Y')} - {hoy.strftime('%d/%m/%Y')}",
            total=total_mes,
            num_tickets=len(tickets_mes),
            promedio_ticket=total_mes / len(tickets_mes) if tickets_mes else 0,
            top_productos=top_productos,
            gastos_por_dia=gastos_por_dia,
            comparacion=comparacion
        )
    
    def _get_top_productos_periodo(self, fecha_inicio, fecha_fin, limit: int = 10) -> List[ProductStats]:
        """Obtiene top productos para un período específico."""
        # Esta implementación requiere acceso directo a la BD
        # En una implementación real, esto iría en la capa de storage
        try:
            if hasattr(self.storage, 'get_connection'):
                with self.storage.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            p.descripcion,
                            SUM(p.cantidad) as cantidad_total,
                            COUNT(DISTINCT t.id) as veces_comprado,
                            ROUND(AVG(p.precio_total), 2) as precio_promedio,
                            ROUND(SUM(p.precio_total), 2) as gasto_total
                        FROM productos p
                        JOIN tickets t ON p.ticket_id = t.id
                        WHERE t.fecha_compra BETWEEN %s AND %s
                        GROUP BY p.descripcion
                        ORDER BY gasto_total DESC
                        LIMIT %s
                    """, (fecha_inicio, fecha_fin, limit))
                    
                    return [
                        ProductStats(
                            descripcion=row[0],
                            cantidad_total=row[1],
                            veces_comprado=row[2],
                            precio_promedio=float(row[3]),
                            gasto_total=float(row[4])
                        )
                        for row in cursor.fetchall()
                    ]
        except Exception as e:
            logger.warning(f"Error obteniendo top productos: {e}")
        
        return []
    
    def _get_gastos_por_dia_semana(self, fecha_inicio, fecha_fin) -> Dict[str, DayStats]:
        """Obtiene gastos por día de la semana."""
        try:
            if hasattr(self.storage, 'get_connection'):
                with self.storage.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            EXTRACT(DOW FROM fecha_compra) as dia_semana,
                            COUNT(*) as num_compras,
                            ROUND(SUM(total), 2) as total_gastado
                        FROM tickets
                        WHERE fecha_compra BETWEEN %s AND %s
                        GROUP BY EXTRACT(DOW FROM fecha_compra)
                        ORDER BY dia_semana
                    """, (fecha_inicio, fecha_fin))
                    
                    dias_nombres = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
                    gastos_por_dia = {}
                    
                    for row in cursor.fetchall():
                        dia_num = int(row[0])
                        gastos_por_dia[dias_nombres[dia_num]] = DayStats(
                            dia=dias_nombres[dia_num],
                            total_gastado=float(row[2]),
                            num_compras=row[1]
                        )
                    
                    return gastos_por_dia
        except Exception as e:
            logger.warning(f"Error obteniendo gastos por día: {e}")
        
        return {}
    
    def _calculate_comparison(self, total_anterior: float, total_actual: float, 
                            periodo_anterior: str) -> ComparisonStats:
        """Calcula estadísticas de comparación entre períodos."""
        diferencia = total_actual - total_anterior
        porcentaje = (diferencia / total_anterior * 100) if total_anterior > 0 else 0
        
        return ComparisonStats(
            periodo_anterior=periodo_anterior,
            total_anterior=total_anterior,
            diferencia=diferencia,
            porcentaje=porcentaje
        )