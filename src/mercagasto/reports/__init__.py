"""
Módulo de reportes por email.
"""

from .generator import ReportGenerator
from .formatters import HTMLReportFormatter
from .email_client import EmailClient
from .reporter import EmailReporter

__all__ = [
    'ReportGenerator',
    'HTMLReportFormatter',
    'EmailClient',
    'EmailReporter'
]