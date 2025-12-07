"""
Servicio principal de reportes por email.
"""

from .generator import ReportGenerator
from .formatters import HTMLReportFormatter
from .email_client import EmailClient
from ..storage import TicketStorageBase
from ..config import get_logger, GmailConfig

logger = get_logger(__name__)


class EmailReporter:
    """Servicio de reportes por email."""
    
    def __init__(self, storage: TicketStorageBase, gmail_config: GmailConfig):
        """
        Inicializa el servicio de reportes.
        
        Args:
            storage: Instancia de almacenamiento
            gmail_config: Configuración de Gmail
        """
        self.generator = ReportGenerator(storage)
        self.formatter = HTMLReportFormatter()
        self.email_client = EmailClient(gmail_config)
    
    def send_weekly_report(self, to: str) -> bool:
        """
        Genera y envía reporte semanal.
        
        Args:
            to: Email destinatario
            
        Returns:
            True si se envió correctamente
        """
        logger.info("Generando reporte semanal...")
        
        try:
            report = self.generator.generate_weekly_report()
            html = self.formatter.format_weekly_email_html(report)
            
            subject = f"🛒 Resumen Semanal Mercadona - {report.total:.2f}€"
            
            success = self.email_client.send_email(to, subject, html)
            
            if success:
                logger.info(f"✓ Reporte semanal enviado a {to}")
            else:
                logger.error(f"✗ Error enviando reporte semanal a {to}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error generando reporte semanal: {e}")
            return False
    
    def send_monthly_report(self, to: str) -> bool:
        """
        Genera y envía reporte mensual.
        
        Args:
            to: Email destinatario
            
        Returns:
            True si se envió correctamente
        """
        logger.info("Generando reporte mensual...")
        
        try:
            report = self.generator.generate_monthly_report()
            html = self.formatter.format_monthly_email_html(report)
            
            subject = f"📊 Resumen Mensual Mercadona - {report.mes} - {report.total:.2f}€"
            
            success = self.email_client.send_email(to, subject, html)
            
            if success:
                logger.info(f"✓ Reporte mensual enviado a {to}")
            else:
                logger.error(f"✗ Error enviando reporte mensual a {to}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error generando reporte mensual: {e}")
            return False