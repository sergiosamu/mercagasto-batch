"""
Extractor de texto de documentos PDF.
"""

import pdfplumber
from typing import Optional

from ..config import get_logger

logger = get_logger(__name__)


class PDFTextExtractor:
    """Extractor de texto de archivos PDF."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF o None si falla
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                logger.info(f"Texto extraído del PDF: {len(text)} caracteres")
                return text.strip() if text else None
                
        except Exception as e:
            logger.error(f"Error extrayendo texto del PDF {pdf_path}: {e}")
            return None
    
    @staticmethod
    def validate_extracted_text(text: str, min_length: int = 100) -> bool:
        """
        Valida que el texto extraído sea válido.
        
        Args:
            text: Texto extraído
            min_length: Longitud mínima requerida
            
        Returns:
            True si el texto es válido
        """
        if not text or len(text.strip()) < min_length:
            logger.warning(f"Texto extraído insuficiente: {len(text) if text else 0} caracteres")
            return False
        
        # Verificar que contenga palabras clave de Mercadona
        keywords = ['MERCADONA', 'FACTURA', 'TOTAL']
        has_keywords = any(keyword in text.upper() for keyword in keywords)
        
        if not has_keywords:
            logger.warning("El texto extraído no contiene palabras clave esperadas")
            return False
        
        return True