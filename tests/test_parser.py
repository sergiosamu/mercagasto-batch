"""
Tests básicos para el parser de Mercadona.
"""

import unittest
from datetime import datetime

from src.mercagasto.parsers import MercadonaTicketParser
from src.mercagasto.models import TicketData


class TestMercadonaTicketParser(unittest.TestCase):
    """Tests para el parser de tickets de Mercadona."""
    
    def setUp(self):
        """Configuración de tests."""
        self.sample_text = """
        MERCADONA, S.A. A-12345678
        C/ EJEMPLO 123
        28000 MADRID
        TELÉFONO: 912345678
        
        01/12/2025 14:30
        OP: 123456789
        FACTURA SIMPLIFICADA: 001-123-456
        
        Descripción                     Importe
        1 PAN DE MOLDE                    2,50
        2 LECHE ENTERA                    1,20    2,40
        3 YOGUR GRIEGO                    0,85    2,55
        
        TOTAL                             7,45€
        
        IVA    BASE IMPONIBLE    CUOTA
        4%     2,40             0,10
        10%    5,05             0,51
        
        TARJETA BANCARIA
        """
    
    def test_parser_basic_info(self):
        """Test parsing de información básica."""
        parser = MercadonaTicketParser(self.sample_text)
        ticket = parser.parse()
        
        self.assertEqual(ticket.store_name, "MERCADONA, S.A.")
        self.assertEqual(ticket.cif, "A-12345678")
        self.assertEqual(ticket.address, "C/ EJEMPLO 123")
        self.assertEqual(ticket.postal_code, "28000")
        self.assertEqual(ticket.city, "MADRID")
        self.assertEqual(ticket.phone, "912345678")
        self.assertEqual(ticket.order_number, "123456789")
        self.assertEqual(ticket.invoice_number, "001-123-456")
        
    def test_parser_products(self):
        """Test parsing de productos."""
        parser = MercadonaTicketParser(self.sample_text)
        ticket = parser.parse()
        
        self.assertEqual(len(ticket.products), 3)
        
        # Primer producto
        p1 = ticket.products[0]
        self.assertEqual(p1.quantity, 1)
        self.assertEqual(p1.description, "PAN DE MOLDE")
        self.assertEqual(p1.total_price, 2.50)
        
        # Segundo producto
        p2 = ticket.products[1]
        self.assertEqual(p2.quantity, 2)
        self.assertEqual(p2.description, "LECHE ENTERA")
        self.assertEqual(p2.unit_price, 1.20)
        self.assertEqual(p2.total_price, 2.40)
    
    def test_parser_total(self):
        """Test parsing del total."""
        parser = MercadonaTicketParser(self.sample_text)
        ticket = parser.parse()
        
        self.assertEqual(ticket.total, 7.45)
        
    def test_ticket_validation(self):
        """Test validación de ticket."""
        parser = MercadonaTicketParser(self.sample_text)
        ticket = parser.parse()
        
        # El total debería ser consistente
        self.assertTrue(ticket.is_total_consistent)


if __name__ == '__main__':
    unittest.main()