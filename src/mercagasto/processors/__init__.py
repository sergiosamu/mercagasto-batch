"""
Módulo de procesadores.
"""

from .file_utils import FileProcessor
from .gmail_client import GmailClient
from .pdf_extractor import PDFTextExtractor
from .gmail_processor import GmailTicketProcessor
from .mercadona_api_client import MercadonaAPIClient, MercadonaProductExtractor
from .product_matcher import ProductMatcher, MatchResult

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