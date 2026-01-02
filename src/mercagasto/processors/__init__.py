"""
Módulo de procesadores.
"""

from .file_utils import FileProcessor
from .gmail_client import GmailClient  # Commented out - requires google dependencies
from .pdf_extractor import PDFTextExtractor  # Commented out - requires pdfplumber
from .gmail_processor import GmailTicketProcessor  # Commented out - depends on gmail_client
from .mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from .product_matcher import ProductMatcher, MatchResult  # Commented out - requires psycopg2

__all__ = [
    'FileProcessor',
    'GmailClient',
    'PDFTextExtractor',
    'GmailTicketProcessor',
    'MercadonaAPIClient',
    'MercadonaProductExtractor',
    'ProductMatcher',
    'MatchResult'
]