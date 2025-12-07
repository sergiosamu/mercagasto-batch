"""
Enumeraciones y estados del sistema.
"""

from enum import Enum


class ProcessingStatus(Enum):
    """Estados posibles de procesamiento de un ticket."""
    PENDING = "pending"           # En espera de procesar
    DOWNLOADING = "downloading"   # Descargando PDF
    EXTRACTING = "extracting"     # Extrayendo texto
    PARSING = "parsing"           # Parseando datos
    VALIDATING = "validating"     # Validando datos
    SAVING = "saving"             # Guardando en BD
    COMPLETED = "completed"       # Completado exitosamente
    FAILED = "failed"             # Falló
    RETRY = "retry"               # Reintento programado