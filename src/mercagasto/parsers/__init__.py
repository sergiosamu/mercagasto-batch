"""
Parsers para diferentes tipos de tickets.
"""

from .base import TicketParserBase
from .mercadona import MercadonaTicketParser
from .formatters import format_ticket

__all__ = [
    'TicketParserBase',
    'MercadonaTicketParser', 
    'format_ticket'
]