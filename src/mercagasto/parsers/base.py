"""
Parser base para tickets de supermercado.
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

from ..models import TicketData, Product
from ..config import get_logger

logger = get_logger(__name__)


class TicketParserBase(ABC):
    """Clase base abstracta para parsers de tickets."""
    
    def __init__(self, text: str):
        """
        Inicializa el parser con el texto del ticket.
        
        Args:
            text: Texto extraído del PDF del ticket
        """
        self.text = text
        self.lines = text.strip().split('\n') if text else []
    
    @abstractmethod
    def parse(self) -> TicketData:
        """
        Parsea el ticket completo y devuelve los datos estructurados.
        
        Returns:
            Objeto TicketData con toda la información del ticket
        """
        pass
    
    @abstractmethod
    def _parse_store_info(self, ticket: TicketData) -> None:
        """Extrae información de la tienda."""
        pass
    
    @abstractmethod
    def _parse_products(self, ticket: TicketData) -> None:
        """Extrae los productos del ticket."""
        pass
    
    @abstractmethod
    def _parse_total(self, ticket: TicketData) -> None:
        """Extrae el total del ticket."""
        pass
    
    def _clean_text(self, text: str) -> str:
        """Limpia y normaliza texto."""
        return text.strip() if text else ""
    
    def _extract_price(self, text: str) -> Optional[float]:
        """
        Extrae precio de un texto.
        
        Args:
            text: Texto que contiene el precio
            
        Returns:
            Precio como float o None si no se encuentra
        """
        match = re.search(r'(\d+,\d+)', text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    def _extract_date(self, text: str, format_str: str = "%d/%m/%Y") -> Optional[datetime]:
        """
        Extrae fecha de un texto.
        
        Args:
            text: Texto que contiene la fecha
            format_str: Formato de la fecha
            
        Returns:
            Objeto datetime o None si no se puede parsear
        """
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), format_str)
            except ValueError:
                logger.warning(f"No se pudo parsear la fecha: {date_match.group(1)}")
        return None