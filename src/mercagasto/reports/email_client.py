"""
Cliente para envío de emails con Gmail API.
"""

import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import get_logger, GmailConfig

logger = get_logger(__name__)


class EmailClient:
    """Cliente para envío de emails usando Gmail API."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, config: GmailConfig):
        """
        Inicializa el cliente de email.
        
        Args:
            config: Configuración de Gmail
        """
        self.credentials_file = config.credentials_file
        self.token_file = config.token_file
        self.service = None
    
    def authenticate(self):
        """Autentica con Gmail para envío de correos."""
        creds = None
        
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("✓ Autenticado con Gmail para envío de correos")
        return self.service
    
    def send_email(self, to: str, subject: str, html_content: str) -> bool:
        """
        Envía un email con HTML.
        
        Args:
            to: Destinatario
            subject: Asunto
            html_content: Contenido HTML
            
        Returns:
            True si se envió correctamente
        """
        if not self.service:
            self.authenticate()
        
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            # Añadir contenido HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # Codificar y enviar
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✓ Email enviado a {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False