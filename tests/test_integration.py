"""
Tests de integración para el parser de tickets.

Estos tests validan que el parsing de PDFs reales funciona correctamente
comparando con resultados esperados.
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime

from src.mercagasto.parsers import MercadonaTicketParser
from src.mercagasto.processors import PDFTextExtractor


class TestTicketParsing:
    """Tests de integración para parsing de tickets."""
    
    @classmethod
    def setup_class(cls):
        """Configuración inicial de la clase de test."""
        cls.test_data_dir = Path(__file__).parent / 'data'
        cls.pdfs_dir = cls.test_data_dir / 'pdfs'
        cls.expected_dir = cls.test_data_dir / 'expected'
        cls.pdf_extractor = PDFTextExtractor()
    
    def get_pdf_files(self):
        """Obtiene lista de archivos PDF para testing."""
        if not self.pdfs_dir.exists():
            return []
        return list(self.pdfs_dir.glob('*.pdf'))
    
    def get_expected_result(self, pdf_name: str):
        """Carga el resultado esperado para un PDF."""
        json_name = pdf_name.replace('.pdf', '.json')
        expected_file = self.expected_dir / json_name
        
        if not expected_file.exists():
            pytest.skip(f"No hay resultado esperado para {pdf_name}")
        
        with open(expected_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalize_ticket_data(self, ticket_data):
        """Normaliza los datos del ticket para comparación."""
        # Convertir datetime a string para comparación
        if hasattr(ticket_data, 'date') and isinstance(ticket_data.date, datetime):
            ticket_data.date = ticket_data.date.strftime('%Y-%m-%d')
        
        # Convertir a dict si es un objeto
        if hasattr(ticket_data, '__dict__'):
            result = {}
            for key, value in ticket_data.__dict__.items():
                if hasattr(value, '__dict__'):
                    # Productos
                    if key == 'products':
                        result[key] = [prod.__dict__ for prod in value]
                    else:
                        result[key] = value.__dict__
                else:
                    result[key] = value
            return result
        
        return ticket_data
    
    @pytest.mark.parametrize("pdf_file", [
        pytest.param(pdf, id=pdf.name) 
        for pdf in (Path(__file__).parent / 'data' / 'pdfs').glob('*.pdf')
        if (Path(__file__).parent / 'data' / 'pdfs').exists()
    ])
    def test_parse_pdf_tickets(self, pdf_file):
        """
        Test parametrizado que valida el parsing de cada PDF.
        
        Args:
            pdf_file: Ruta al archivo PDF a testear
        """
        # Saltar si no hay PDFs
        if not pdf_file.exists():
            pytest.skip("No hay archivos PDF para testear")
        
        # Extraer texto del PDF
        text = self.pdf_extractor.extract_text_from_pdf(str(pdf_file))
        assert text is not None, f"No se pudo extraer texto de {pdf_file.name}"
        assert len(text.strip()) > 50, f"Texto extraído muy corto en {pdf_file.name}"
        
        # Parsear ticket
        parser = MercadonaTicketParser(text)
        ticket = parser.parse()
        
        # Validaciones básicas
        assert ticket.total > 0, f"Total inválido en {pdf_file.name}"
        assert len(ticket.products) > 0, f"Sin productos en {pdf_file.name}"
        assert ticket.invoice_number, f"Sin número de factura en {pdf_file.name}"
        
        # Cargar resultado esperado
        expected = self.get_expected_result(pdf_file.name)
        
        # Normalizar datos
        actual = self.normalize_ticket_data(ticket)
        
        # Comparaciones específicas
        assert actual['total'] == expected['total'], f"Total no coincide en {pdf_file.name}"
        assert actual['invoice_number'] == expected['invoice_number'], f"Factura no coincide en {pdf_file.name}"
        assert len(actual['products']) == len(expected['products']), f"Número de productos no coincide en {pdf_file.name}"
        
        # Validar productos
        for i, (actual_prod, expected_prod) in enumerate(zip(actual['products'], expected['products'])):
            assert actual_prod['quantity'] == expected_prod['quantity'], f"Cantidad producto {i} en {pdf_file.name}"
            assert actual_prod['total_price'] == expected_prod['total_price'], f"Precio producto {i} en {pdf_file.name}"
    
    def test_pdf_directory_exists(self):
        """Verifica que exista el directorio de PDFs."""
        assert self.pdfs_dir.exists(), f"Directorio {self.pdfs_dir} no existe"
    
    def test_has_test_pdfs(self):
        """Verifica que haya al menos un PDF para testear."""
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            pytest.skip("No hay archivos PDF en tests/data/pdfs/ para testear")
        assert len(pdf_files) > 0, "Deberían existir archivos PDF para testing"
    
    def test_expected_results_exist(self):
        """Verifica que existan resultados esperados para los PDFs."""
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            pytest.skip("No hay archivos PDF para verificar")
        
        missing_expected = []
        for pdf_file in pdf_files:
            json_name = pdf_file.name.replace('.pdf', '.json')
            expected_file = self.expected_dir / json_name
            if not expected_file.exists():
                missing_expected.append(json_name)
        
        if missing_expected:
            pytest.skip(f"Faltan archivos esperados: {missing_expected}")
    
    def test_parser_error_handling(self):
        """Test de manejo de errores del parser."""
        # Texto vacío
        parser = MercadonaTicketParser("")
        ticket = parser.parse()
        assert ticket.total == 0.0
        
        # Texto inválido
        parser = MercadonaTicketParser("Texto que no es un ticket")
        ticket = parser.parse()
        assert ticket.total == 0.0


class TestPDFExtraction:
    """Tests para extracción de PDFs."""
    
    def test_pdf_extractor_exists(self):
        """Verifica que el extractor funcione."""
        extractor = PDFTextExtractor()
        assert extractor is not None
    
    @pytest.mark.parametrize("pdf_file", [
        pytest.param(pdf, id=pdf.name) 
        for pdf in (Path(__file__).parent / 'data' / 'pdfs').glob('*.pdf')
        if (Path(__file__).parent / 'data' / 'pdfs').exists()
    ])
    def test_pdf_text_extraction(self, pdf_file):
        """Test de extracción de texto de PDFs."""
        if not pdf_file.exists():
            pytest.skip("No hay archivos PDF para testear")
        
        extractor = PDFTextExtractor()
        text = extractor.extract_text_from_pdf(str(pdf_file))
        
        assert text is not None, f"No se pudo extraer texto de {pdf_file.name}"
        assert len(text.strip()) > 0, f"Texto extraído vacío en {pdf_file.name}"
        assert 'MERCADONA' in text.upper(), f"No se encontró MERCADONA en {pdf_file.name}"


if __name__ == '__main__':
    # Ejecutar tests si se ejecuta directamente
    pytest.main([__file__, '-v'])