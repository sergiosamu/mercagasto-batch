"""
Configuración del sistema.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    """Configuración de la base de datos PostgreSQL."""
    host: str = 'localhost'
    port: int = 5432
    database: str = 'mercadona'
    user: str = 'postgres'
    password: str = 'postgres'
    sslmode: str = 'prefer'
    connect_timeout: int = 30
    application_name: str = 'mercagasto-batch'
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Crea configuración desde variables de entorno."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'mercadona'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            sslmode=os.getenv('DB_SSLMODE', 'prefer'),
            connect_timeout=int(os.getenv('DB_CONNECT_TIMEOUT', '30')),
            application_name=os.getenv('DB_APP_NAME', 'mercagasto-batch')
        )
    
    @classmethod
    def from_url(cls, database_url: str) -> 'DatabaseConfig':
        """Crea configuración desde DATABASE_URL (formato Render/Heroku)."""
        import urllib.parse as urlparse
        
        url = urlparse.urlparse(database_url)
        return cls(
            host=url.hostname or 'localhost',
            port=url.port or 5432,
            database=url.path.lstrip('/') if url.path else 'mercadona',
            user=url.username or 'postgres',
            password=url.password or 'postgres',
            sslmode='require' if 'render' in (url.hostname or '') else 'prefer',
            connect_timeout=30,
            application_name='mercagasto-batch'
        )


def get_database_config() -> DatabaseConfig:
    """
    Obtiene la configuración de base de datos.
    Prioriza DATABASE_URL sobre variables individuales.
    """
    from .logging import get_logger
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        logger = get_logger(__name__)
        logger.info("Usando DATABASE_URL para configuración de BD")
        return DatabaseConfig.from_url(database_url)
    else:
        return DatabaseConfig.from_env()


@dataclass
class GmailConfig:
    """Configuración de Gmail API."""
    credentials_file: str = 'credentials.json'
    token_file: str = 'token.pickle'
    
    @classmethod
    def from_env(cls) -> 'GmailConfig':
        """Crea configuración desde variables de entorno."""
        return cls(
            credentials_file=os.getenv('GMAIL_CREDENTIALS', 'credentials.json'),
            token_file=os.getenv('GMAIL_TOKEN', 'token.pickle')
        )


@dataclass
class ProcessingConfig:
    """Configuración del procesamiento."""
    backup_dir: str = 'ticket_backups'
    max_retries: int = 3
    mark_as_read: bool = True
    add_label: bool = True
    delete_pdf: bool = False
    
    @classmethod
    def from_env(cls) -> 'ProcessingConfig':
        """Crea configuración desde variables de entorno."""
        return cls(
            backup_dir=os.getenv('BACKUP_DIR', 'ticket_backups'),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            mark_as_read=os.getenv('MARK_AS_READ', 'true').lower() == 'true',
            add_label=os.getenv('ADD_LABEL', 'true').lower() == 'true',
            delete_pdf=os.getenv('DELETE_PDF', 'false').lower() == 'true'
        )


@dataclass
class AppConfig:
    """Configuración principal de la aplicación."""
    database: DatabaseConfig
    gmail: GmailConfig
    processing: ProcessingConfig
    log_dir: str = 'logs'
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Crea configuración completa desde variables de entorno."""
        return cls(
            database=DatabaseConfig.from_env(),
            gmail=GmailConfig.from_env(),
            processing=ProcessingConfig.from_env(),
            log_dir=os.getenv('LOG_DIR', 'logs')
        )