"""
Cliente para interactuar con Gmail API.
"""

import os
import base64
import pickle
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import get_logger, GmailConfig

logger = get_logger(__name__)


class GmailClient:
    """Cliente para interactuar con Gmail API."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, config: GmailConfig):
        """
        Inicializa el cliente de Gmail.
        
        Args:
            config: Configuración de Gmail
        """
        self.credentials_file = config.credentials_file
        self.token_file = config.token_file
        self.service = None
    
    def authenticate(self):
        """Autentica con Gmail usando OAuth2."""
        creds = None
        
        # Cargar token existente
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas, autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Guardar token para futuros usos
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("✓ Autenticado con Gmail correctamente")
        return self.service
    
    def search_emails(self, query: str = 'from:noreply@mercadona.es has:attachment', 
                     max_results: int = 10, unread_only: bool = True) -> List[Dict[str, str]]:
        """
        Busca correos según una query.
        
        Args:
            query: Query de búsqueda de Gmail
            max_results: Número máximo de resultados
            unread_only: Solo correos no leídos
            
        Returns:
            Lista de mensajes encontrados
        """
        if not self.service:
            self.authenticate()
        
        if unread_only:
            query += ' is:unread'
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Encontrados {len(messages)} correos de Mercadona")
            return messages
        
        except Exception as e:
            logger.error(f"Error buscando correos: {e}")
            return []
    
    def get_message_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene los adjuntos PDF de un mensaje.
        
        Args:
            message_id: ID del mensaje de Gmail
            
        Returns:
            Lista de información de adjuntos
        """
        if not self.service:
            self.authenticate()
        
        attachments = []
        
        try:
            # Obtener mensaje completo
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Buscar adjuntos
            parts = message['payload'].get('parts', [])
            
            for part in parts:
                filename = part.get('filename', '')
                if filename.lower().endswith('.pdf'):
                    attachment_id = part['body'].get('attachmentId')
                    
                    if attachment_id:
                        # Descargar adjunto
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        
                        # Decodificar contenido
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        
                        attachments.append({
                            'filename': filename,
                            'content': file_data,
                            'size': len(file_data)
                        })
                        
                        logger.info(f"Descargado adjunto: {filename} ({len(file_data)} bytes)")
            
            return attachments
        
        except Exception as e:
            logger.error(f"Error obteniendo adjuntos del mensaje {message_id}: {e}")
            return []
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Marca un correo como leído.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            True si se marcó correctamente
        """
        if not self.service:
            self.authenticate()
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"Correo {message_id} marcado como leído")
            return True
        except Exception as e:
            logger.error(f"Error marcando como leído: {e}")
            return False
    
    def add_label(self, message_id: str, label_name: str = 'Mercadona/Procesado') -> bool:
        """
        Añade una etiqueta al correo.
        
        Args:
            message_id: ID del mensaje
            label_name: Nombre de la etiqueta
            
        Returns:
            True si se añadió correctamente
        """
        if not self.service:
            self.authenticate()
        
        try:
            # Buscar o crear etiqueta
            label_id = self._get_or_create_label(label_name)
            
            if label_id:
                # Añadir etiqueta
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
                logger.info(f"Etiqueta '{label_name}' añadida al mensaje {message_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error añadiendo etiqueta: {e}")
            return False
    
    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """Busca o crea una etiqueta."""
        try:
            # Buscar etiqueta existente
            labels = self.service.users().labels().list(userId='me').execute()
            
            for label in labels.get('labels', []):
                if label['name'] == label_name:
                    return label['id']
            
            # Crear etiqueta si no existe
            label = self.service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            
            logger.info(f"Etiqueta '{label_name}' creada")
            return label['id']
        
        except Exception as e:
            logger.error(f"Error manejando etiqueta {label_name}: {e}")
            return None