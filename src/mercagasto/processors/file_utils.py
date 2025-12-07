"""
Utilidades para procesamiento de archivos.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple

from ..config import get_logger

logger = get_logger(__name__)


class FileProcessor:
    """Utilidades para procesamiento de archivos."""
    
    def __init__(self, backup_dir: str):
        """
        Inicializa el procesador de archivos.
        
        Args:
            backup_dir: Directorio base para backups
        """
        self.backup_dir = Path(backup_dir)
        self._create_backup_directories()
    
    def _create_backup_directories(self):
        """Crea la estructura de directorios de backup."""
        self.backup_dir.mkdir(exist_ok=True)
        (self.backup_dir / 'pdfs').mkdir(exist_ok=True)
        (self.backup_dir / 'text').mkdir(exist_ok=True)
        (self.backup_dir / 'failed').mkdir(exist_ok=True)
        
        logger.info(f"Directorios de backup configurados en: {self.backup_dir}")
    
    @staticmethod
    def calculate_file_hash(filepath: str) -> str:
        """
        Calcula hash SHA-256 de un archivo.
        
        Args:
            filepath: Ruta al archivo
            
        Returns:
            Hash hexadecimal del archivo
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash de {filepath}: {e}")
            return ""
    
    def save_file_with_backup(self, content: bytes, filename: str, 
                             subdir: str = 'pdfs') -> Tuple[str, str, int]:
        """
        Guarda un archivo con backup seguro.
        
        Args:
            content: Contenido del archivo
            filename: Nombre del archivo
            subdir: Subdirectorio donde guardar
            
        Returns:
            (filepath, file_hash, file_size)
        """
        from datetime import datetime
        
        # Crear nombre único con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        filepath = self.backup_dir / subdir / safe_filename
        
        # Guardar archivo
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Calcular hash y tamaño
        file_hash = self.calculate_file_hash(str(filepath))
        file_size = os.path.getsize(filepath)
        
        logger.info(f"Archivo guardado: {filepath} (hash: {file_hash[:8]}..., size: {file_size} bytes)")
        
        return str(filepath), file_hash, file_size
    
    def save_text_backup(self, text: str, processing_id: int) -> str:
        """
        Guarda backup del texto extraído.
        
        Args:
            text: Texto a guardar
            processing_id: ID del procesamiento
            
        Returns:
            Ruta al archivo guardado
        """
        filename = f"text_{processing_id}.txt"
        filepath = self.backup_dir / 'text' / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.info(f"Texto guardado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error guardando texto: {e}")
            return ""
    
    def move_to_failed(self, source_path: str) -> str:
        """
        Mueve un archivo a la carpeta de fallidos.
        
        Args:
            source_path: Ruta del archivo fuente
            
        Returns:
            Ruta del archivo en la carpeta de fallidos
        """
        try:
            failed_path = self.backup_dir / 'failed' / os.path.basename(source_path)
            shutil.copy2(source_path, failed_path)
            logger.info(f"Archivo movido a fallidos: {failed_path}")
            return str(failed_path)
        except Exception as e:
            logger.error(f"Error moviendo archivo a fallidos: {e}")
            return ""