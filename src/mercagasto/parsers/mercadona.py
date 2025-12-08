"""
Parser específico para tickets de Mercadona.
"""

import re
from datetime import datetime
from typing import Optional

from .base import TicketParserBase
from ..models import TicketData, Product
from ..config import get_logger

logger = get_logger(__name__)


class MercadonaTicketParser(TicketParserBase):
    """Parser especializado para tickets de Mercadona."""
    
    def parse(self) -> TicketData:
        """Parsea el ticket completo de Mercadona."""
        ticket = TicketData(
            store_name="",
            cif="",
            address="",
            postal_code="",
            city="",
            phone="",
            date=None,
            time="",
            order_number="",
            invoice_number="",
            products=[],
            total=0.0,
            payment_method="",
            iva_breakdown={}
        )
        
        try:
            # Parsear información de la tienda
            self._parse_store_info(ticket)
            
            # Parsear productos
            self._parse_products(ticket)
            
            # Parsear total
            self._parse_total(ticket)
            
            # Parsear IVA
            self._parse_iva(ticket)
            
            # Parsear método de pago
            self._parse_payment_method(ticket)
            
            logger.info(f"Ticket parseado: {ticket.invoice_number}, {len(ticket.products)} productos, {ticket.total}€")
            
            # Debug logging si no hay número de factura
            if not ticket.invoice_number:
                logger.warning("No se encontró número de factura. Buscando en todo el texto...")
                self._debug_invoice_number_search()
            
        except Exception as e:
            logger.error(f"Error parseando ticket de Mercadona: {e}")
            raise
        
        return ticket
    
    def _debug_invoice_number_search(self) -> None:
        """Debug para buscar posibles números de factura en el texto."""
        logger.debug("=== DEBUG: Búsqueda de número de factura ===")
        
        for i, line in enumerate(self.lines, 1):
            line_clean = self._clean_text(line)
            
            # Buscar líneas que contengan palabras relacionadas con factura
            if any(keyword in line_clean.upper() for keyword in ['FACTURA', 'FAC', 'INVOICE']):
                logger.debug(f"Línea {i}: {line_clean}")
            
            # Buscar patrones de números que podrían ser facturas
            if re.search(r'\d{3,}-\d+-\d+', line_clean):
                logger.debug(f"Patrón XXX-X-X en línea {i}: {line_clean}")
            
            if re.search(r'\d{8,}', line_clean):
                logger.debug(f"Número largo en línea {i}: {line_clean}")
        
        logger.debug("=== FIN DEBUG ===")
    
    
    def _parse_store_info(self, ticket: TicketData) -> None:
        """Extrae información de la tienda Mercadona."""
        for line in self.lines:
            line = self._clean_text(line)
            
            # Nombre y CIF de Mercadona
            if "MERCADONA" in line and "A-" in line:
                match = re.search(r'MERCADONA.*?A-(\d+)', line)
                if match:
                    ticket.store_name = "MERCADONA, S.A."
                    ticket.cif = f"A-{match.group(1)}"
            
            # Dirección
            elif "C/" in line or "HUMANES" in line:
                ticket.address = line
            
            # Código postal y ciudad
            elif re.match(r'\d{5}\s+\w+', line):
                parts = line.split()
                ticket.postal_code = parts[0]
                ticket.city = ' '.join(parts[1:])
            
            # Teléfono
            elif "TELÉFONO:" in line:
                match = re.search(r'(\d{9})', line)
                if match:
                    ticket.phone = match.group(1)
            
            # Fecha y hora
            elif re.match(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', line):
                parts = line.split()
                if len(parts) >= 2:
                    ticket.date = self._extract_date(parts[0])
                    ticket.time = parts[1]
            
            # Número de operación
            elif "OP:" in line:
                match = re.search(r'OP:\s*(\d+)', line)
                if match:
                    ticket.order_number = match.group(1)
            
            # Número de factura - Múltiples patrones
            elif "FACTURA SIMPLIFICADA:" in line:
                # Patrón: FACTURA SIMPLIFICADA: 123-456-789
                match = re.search(r'(\d+-\d+-\d+)', line)
                if match:
                    ticket.invoice_number = match.group(1)
            elif "FACTURA:" in line:
                # Patrón: FACTURA: 123456789
                match = re.search(r'FACTURA:\s*(\d+)', line)
                if match:
                    ticket.invoice_number = match.group(1)
            elif re.search(r'Nº\s*(?:FACTURA|FAC):', line, re.IGNORECASE):
                # Patrón: Nº FACTURA: 123-456-789
                match = re.search(r'(\d+-\d+-\d+|\d+)', line)
                if match:
                    ticket.invoice_number = match.group(1)
            elif re.search(r'(\d+-\d+-\d+)', line) and not ticket.invoice_number:
                # Patrón genérico de números con guiones (como último recurso)
                # Solo si no hay productos parseados aún para evitar falsos positivos
                if not ticket.products:
                    match = re.search(r'(\d+-\d+-\d+)', line)
                    if match:
                        ticket.invoice_number = match.group(1)
    
    def _parse_products(self, ticket: TicketData) -> None:
        """Extrae los productos del ticket de Mercadona."""
        in_products = False
        
        for line in self.lines:
            line = self._clean_text(line)
            
            # Detectar inicio de productos
            if "Descripción" in line and "Importe" in line:
                in_products = True
                continue
            
            # Detectar fin de productos
            if "TOTAL" in line and "€" in line:
                in_products = False
                continue
            
            if not in_products or not line:
                continue
            
            # Parsear línea de producto
            product = self._parse_product_line(line)
            if product:
                ticket.products.append(product)
                logger.debug(f"Producto parseado: {product.description} - {product.total_price}€")
    
    def _parse_product_line(self, line: str) -> Optional[Product]:
        """
        Parsea una línea de producto de Mercadona.
        
        Formatos esperados:
        - "1 CHULETA PAVO 4,20"
        - "2 YOGUR GRIEGO LIGERO 1,55 3,10"
        """
        parts = line.split()
        if len(parts) < 2:
            return None
        
        try:
            quantity = int(parts[0])
        except ValueError:
            return None
        
        # Buscar precios (números con coma)
        prices ]
        price_indices = []
        for i, part in enumerate(parts):
            # Verificar que sea un número con coma y no contenga letras
            if re.match(r'^\d+,\d+$', part):
                prices.append(float(part.replace(',', '.')))
                price_indices.append(i)
        
        if not prices:
            return None
        
        # La descripción está entre la cantidad y el primer precio
        if price_indices:
            desc_parts = parts[1:price_indices[0]]
            description = ' '.join(desc_parts)
        else:
            return None
        
        # Verificar si hay peso
        weight = None
        if 'kg' in line or '€/kg' in line:
            weight_match = re.search(r'(\d+,\d+)\s*kg', line)
            if weight_match:
                weight = weight_match.group(1) + ' kg'
        
        # Si hay dos precios, el primero es unitario y el segundo total
        if len(prices) == 2:
            unit_price = prices[0]
            total_price = prices[1]
        else:
            unit_price = None
            total_price = prices[0]
        
        try:
            return Product(
                quantity=quantity,
                description=description,
                unit_price=unit_price,
                total_price=total_price,
                weight=weight
            )
        except ValueError as e:
            logger.warning(f"Error creando producto: {e}")
            return None
    
    def _parse_total(self, ticket: TicketData) -> None:
        """Extrae el total del ticket."""
        for line in self.lines:
            if "TOTAL" in line and "€" in line:
                price = self._extract_price(line)
                if price:
                    ticket.total = price
                    break
    
    def _parse_iva(self, ticket: TicketData) -> None:
        """Extrae el desglose de IVA."""
        iva_section = False
        for line in self.lines:
            line = self._clean_text(line)
            
            if "IVA" in line and "BASE IMPONIBLE" in line:
                iva_section = True
                continue
            
            if iva_section and re.match(r'\d+%', line):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        rate = parts[0]
                        base = float(parts[1].replace(',', '.'))
                        quota = float(parts[2].replace(',', '.'))
                        ticket.iva_breakdown[rate] = {
                            'base': base,
                            'cuota': quota
                        }
                    except (ValueError, IndexError):
                        logger.warning(f"Error parseando línea de IVA: {line}")
    
    def _parse_payment_method(self, ticket: TicketData) -> None:
        """Extrae el método de pago."""
        for line in self.lines:
            if "TARJETA BANCARIA" in line:
                ticket.payment_method = "TARJETA BANCARIA"
                break
            elif "EFECTIVO" in line:
                ticket.payment_method = "EFECTIVO"
                break