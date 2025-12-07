"""
Clase base para almacenamiento de tickets.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from contextlib import contextmanager

from ..models import TicketData


class TicketStorageBase(ABC):
    """Clase base abstracta para almacenamiento de tickets."""
    
    @abstractmethod
    def create_tables(self) -> None:
        """Crea las tablas necesarias en el almacén."""
        pass
    
    @abstractmethod
    def save_ticket(self, ticket: TicketData) -> int:
        """
        Guarda un ticket en el almacén.
        
        Args:
            ticket: Datos del ticket a guardar
            
        Returns:
            ID del ticket guardado
        """
        pass
    
    @abstractmethod
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un ticket por su ID.
        
        Args:
            ticket_id: ID del ticket
            
        Returns:
            Datos del ticket o None si no existe
        """
        pass
    
    @abstractmethod
    def validate_ticket(self, ticket: TicketData) -> Tuple[bool, List[str]]:
        """
        Valida un ticket antes de guardarlo.
        
        Args:
            ticket: Ticket a validar
            
        Returns:
            (es_valido, lista_de_errores)
        """
        pass
    
    @abstractmethod
    def get_tickets_by_date_range(self, fecha_inicio: str, fecha_fin: str) -> List[Dict[str, Any]]:
        """
        Obtiene tickets en un rango de fechas.
        
        Args:
            fecha_inicio: Fecha de inicio (YYYY-MM-DD)
            fecha_fin: Fecha de fin (YYYY-MM-DD)
            
        Returns:
            Lista de tickets
        """
        pass
    
    @abstractmethod
    def get_total_gastado(self, fecha_inicio: str = None, fecha_fin: str = None) -> float:
        """
        Calcula el total gastado en un período.
        
        Args:
            fecha_inicio: Fecha de inicio opcional
            fecha_fin: Fecha de fin opcional
            
        Returns:
            Total gastado
        """
        pass