"""
Procesador principal de tickets desde Gmail.
"""

import json
import traceback
from typing import Dict, Any, List
from datetime import datetime

from .gmail_client import GmailClient
from .pdf_extractor import PDFTextExtractor
from .file_utils import FileProcessor
from ..parsers import MercadonaTicketParser
from ..storage import TicketStorageBase, PostgreSQLTicketStorage
from ..models import ProcessingStatus
from ..config import get_logger, GmailConfig, ProcessingConfig

logger = get_logger(__name__)


class GmailTicketProcessor:
    """Procesador principal de tickets desde Gmail."""
    
    def __init__(self, storage: TicketStorageBase, gmail_config: GmailConfig, 
                 processing_config: ProcessingConfig):
        """
        Inicializa el procesador.
        
        Args:
            storage: Instancia de almacenamiento
            gmail_config: Configuración de Gmail
            processing_config: Configuración de procesamiento
        """
        self.storage = storage
        self.config = processing_config
        self.gmail_client = GmailClient(gmail_config)
        self.pdf_extractor = PDFTextExtractor()
        self.file_processor = FileProcessor(processing_config.backup_dir)
        
        logger.info("Procesador de Gmail inicializado")
    
    def process_all_tickets(self, retry_failed: bool = True) -> Dict[str, Any]:
        """
        Procesa todos los tickets de Mercadona en Gmail.
        
        Args:
            retry_failed: Si reintentar tickets que fallaron anteriormente
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        stats = {
            'correos_encontrados': 0,
            'pdfs_descargados': 0,
            'tickets_procesados': 0,
            'tickets_guardados': 0,
            'tickets_duplicados': 0,
            'tickets_invalidos': 0,
            'tickets_descartados': 0,
            'reintentos_exitosos': 0,
            'errores': 0,
            'errores_detalle': []
        }
        
        # Autenticar con Gmail
        self.gmail_client.authenticate()
        
        # Reintentar tickets fallidos si se solicita
        if retry_failed and isinstance(self.storage, PostgreSQLTicketStorage):
            self._retry_failed_tickets(stats)
        
        # Procesar correos nuevos
        self._process_new_emails(stats)
        
        # Mostrar resumen
        self._print_summary(stats)
        
        return stats
    
    def _retry_failed_tickets(self, stats: Dict[str, Any]):
        """Reintenta tickets que fallaron anteriormente."""
        logger.info("Verificando tickets fallidos para reintentar...")
        
        failed = self.storage.get_failed_processings(self.config.max_retries)
        
        if failed:
            logger.info(f"Encontrados {len(failed)} tickets fallidos para reintentar")
            print(f"\n🔄 Reintentando {len(failed)} tickets fallidos...")
            
            for f in failed:
                try:
                    # Obtener email del subscriptor para el processing_id
                    subscriptor_email = None
                    if isinstance(self.storage, PostgreSQLTicketStorage):
                        subscriptor_email = self.storage.get_subscriptor_email_by_processing_id(f['id'])
                    
                    result = self._process_single_pdf(
                        f['pdf_path'], f['message_id'], processing_id=f['id'], 
                        subscriptor_email=subscriptor_email
                    )
                    if result['status'] == 'success':
                        stats['reintentos_exitosos'] += 1
                        
                except Exception as e:
                    logger.error(f"Error en reintento: {e}")
                    stats['errores'] += 1
                    stats['errores_detalle'].append({'retry_error': str(e)})
    
    def _process_new_emails(self, stats: Dict[str, Any]):
        """Procesa correos nuevos."""
        messages = self.gmail_client.search_emails(unread_only=True)
        stats['correos_encontrados'] = len(messages)
        
        if not messages:
            logger.info("📭 No hay correos nuevos de Mercadona")
            print("\\n📭 No hay correos nuevos de Mercadona")
            return
        
        logger.info(f"📧 Procesando {len(messages)} correos nuevos...")
        print(f"\\n📧 Procesando {len(messages)} correos...")
        print("=" * 60)
        
        for msg in messages:
            message_id = msg['id']
            logger.info(f"Procesando correo ID: {message_id}")
            print(f"\\n📨 Procesando correo ID: {message_id}")
            
            try:
                self._process_single_email(message_id, stats)
                
            except Exception as e:
                logger.error(f"Error procesando correo {message_id}: {e}")
                stats['errores'] += 1
                stats['errores_detalle'].append({
                    'message_id': message_id,
                    'error': str(e)
                })
    
    def _process_single_email(self, message_id: str, stats: Dict[str, Any]):
        """Procesa un único email."""
        # Obtener remitente
        sender_email = self.gmail_client.get_sender_email(message_id)
        # Comprobar en la base de datos si está subscrito
        is_subscribed = False
        if isinstance(self.storage, PostgreSQLTicketStorage):
            is_subscribed = self.storage.is_email_subscribed(sender_email)
        else:
            logger.warning("El almacenamiento no es PostgreSQL, no se puede comprobar subscripción.")

        if not is_subscribed:
            logger.info(f"Remitente {sender_email} no subscrito. Etiquetando como #notsubscribed.")
            print(f"  ⚠ Remitente {sender_email} no subscrito. Email ignorado.")
            stats['tickets_descartados'] += 1
            if self.config.mark_as_read:
                self.gmail_client.mark_as_read(message_id)
            try:
                self.gmail_client.add_label(message_id, label_name='#notsubscribed')
            except TypeError:
                self.gmail_client.add_label(message_id)
            return

        # Descargar adjuntos
        attachments = self.gmail_client.get_message_attachments(message_id)
        # Filtrar solo PDFs cuyo nombre contenga 'Mercadona'
        filtered_attachments = [
            att for att in attachments
            if att['filename'].lower().endswith('.pdf') and 'mercadona' in att['filename'].lower()
        ]
        stats['pdfs_descargados'] += len(filtered_attachments)

        if not filtered_attachments:
            logger.info("No hay PDFs de Mercadona para procesar en este correo.")
            print("  ⚠ No hay PDFs de Mercadona para procesar en este correo.")
            stats['tickets_descartados'] += 1
            # Marcar como leído y añadir etiqueta 'invalid'
            if self.config.mark_as_read:
                self.gmail_client.mark_as_read(message_id)
            try:
                self.gmail_client.add_label(message_id, label_name='invalid')
            except TypeError:
                self.gmail_client.add_label(message_id)
            return

        # Procesar cada PDF válido
        for attachment in filtered_attachments:
            logger.info(f"Procesando PDF: {attachment['filename']}")
            print(f"\n  📄 Procesando: {attachment['filename']}")

            # Guardar PDF con backup
            pdf_path, pdf_hash, pdf_size = self.file_processor.save_file_with_backup(
                attachment['content'], attachment['filename']
            )

            # Registrar procesamiento si es PostgreSQL
            processing_id = None
            if isinstance(self.storage, PostgreSQLTicketStorage):
                processing_id = self.storage.start_processing(
                    message_id, attachment['filename'], pdf_hash, pdf_path, sender_email
                )

                self.storage.register_file_backup(
                    processing_id, 'pdf', pdf_path, pdf_hash, pdf_size
                )

            # Procesar PDF
            result = self._process_single_pdf(pdf_path, message_id, processing_id, sender_email)

            # Actualizar estadísticas
            self._update_stats_from_result(result, stats, attachment['filename'])

        # Marcar como leído y añadir etiqueta
        if self.config.mark_as_read:
            self.gmail_client.mark_as_read(message_id)

        if self.config.add_label:
            self.gmail_client.add_label(message_id)
    
    def _process_single_pdf(self, pdf_path: str, message_id: str, 
                           processing_id: int = None, subscriptor_email: str = None) -> Dict[str, Any]:
        """Procesa un único archivo PDF."""
        result = {'status': 'error', 'error': None, 'ticket_id': None}
        
        try:
            # Actualizar estado: extrayendo
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                self.storage.update_processing_status(processing_id, ProcessingStatus.EXTRACTING)
            
            # Extraer texto del PDF
            text = self.pdf_extractor.extract_text_from_pdf(pdf_path)
            
            if not self.pdf_extractor.validate_extracted_text(text):
                error_msg = "Texto extraído insuficiente o inválido"
                self._handle_processing_error(processing_id, 'extraction', error_msg, result)
                return result
            
            # Guardar backup del texto
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                text_path = self.file_processor.save_text_backup(text, processing_id)
                file_hash = FileProcessor.calculate_file_hash(text_path) if text_path else ""
                
                if text_path:
                    self.storage.register_file_backup(
                        processing_id, 'text', text_path, file_hash, len(text.encode())
                    )
                    self.storage.update_processing_status(
                        processing_id, ProcessingStatus.EXTRACTING, extracted_text_path=text_path
                    )
            
            # Parsear ticket
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                self.storage.update_processing_status(processing_id, ProcessingStatus.PARSING)
            
            parser = MercadonaTicketParser(text)
            ticket = parser.parse()
            
            # Validar ticket
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                self.storage.update_processing_status(processing_id, ProcessingStatus.VALIDATING)
            
            is_valid, errors = self.storage.validate_ticket(ticket)
            if not is_valid:
                error_msg = f"Ticket inválido: {'; '.join(errors)}"
                self._handle_processing_error(processing_id, 'validation', error_msg, result)
                result['status'] = 'invalid'
                self.file_processor.move_to_failed(pdf_path)
                return result
            
            # Guardar en base de datos
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                self.storage.update_processing_status(processing_id, ProcessingStatus.SAVING)
            
            ticket_id = self.storage.save_ticket(ticket, subscriptor_email)
            
            # Completar procesamiento
            if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                self.storage.update_processing_status(
                    processing_id, ProcessingStatus.COMPLETED, ticket_id=ticket_id
                )
            
            logger.info(f"✓ Ticket procesado exitosamente - ID: {ticket_id}")
            print(f"  ✓ Ticket guardado en BD (ID: {ticket_id})")
            
            result['status'] = 'success'
            result['ticket_id'] = ticket_id
            
        except Exception as e:
            error_str = str(e)
            
            # Verificar si es un duplicado
            if 'duplicate' in error_str.lower() or 'already exists' in error_str.lower():
                logger.info(f"Ticket duplicado detectado")
                print(f"  ⚠ Ticket duplicado (factura ya existe)")
                
                if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
                    self.storage.update_processing_status(
                        processing_id, ProcessingStatus.COMPLETED, error_message="Duplicado"
                    )
                
                result['status'] = 'duplicate'
            else:
                error_trace = traceback.format_exc()
                logger.error(f"Error procesando PDF: {error_str}")
                logger.error(error_trace)
                print(f"  ✗ Error: {error_str}")
                
                self._handle_processing_error(processing_id, 'processing', error_str, result)
                self.file_processor.move_to_failed(pdf_path)
        
        return result
    
    def _handle_processing_error(self, processing_id: int, stage: str, 
                                error_msg: str, result: Dict[str, Any]):
        """Maneja errores de procesamiento."""
        if processing_id and isinstance(self.storage, PostgreSQLTicketStorage):
            self.storage.update_processing_status(
                processing_id, ProcessingStatus.RETRY,
                error_stage=stage,
                error_message=error_msg,
                error_traceback=traceback.format_exc()
            )
        
        result['status'] = 'error'
        result['error'] = error_msg
    
    def _update_stats_from_result(self, result: Dict[str, Any], stats: Dict[str, Any], 
                                 filename: str):
        """Actualiza estadísticas basándose en el resultado."""
        if result['status'] == 'success':
            stats['tickets_procesados'] += 1
            stats['tickets_guardados'] += 1
        elif result['status'] == 'duplicate':
            stats['tickets_duplicados'] += 1
        elif result['status'] == 'invalid':
            stats['tickets_invalidos'] += 1
        elif result['status'] == 'error':
            stats['errores'] += 1
            stats['errores_detalle'].append({
                'file': filename,
                'error': result['error']
            })
    
    def _print_summary(self, stats: Dict[str, Any]):
        """Imprime resumen de estadísticas."""
        print("\\n" + "="*60)
        print("📊 RESUMEN DEL PROCESAMIENTO")
        print("="*60)
        print(f"✉️  Correos encontrados: {stats['correos_encontrados']}")
        print(f"📎 PDFs descargados: {stats['pdfs_descargados']}")
        print(f"🎫 Tickets procesados: {stats['tickets_procesados']}")
        print(f"💾 Tickets guardados en BD: {stats['tickets_guardados']}")
        print(f"🔄 Reintentos exitosos: {stats['reintentos_exitosos']}")
        print(f"⚠️  Tickets duplicados: {stats['tickets_duplicados']}")
        print(f"⚠️  Tickets inválidos: {stats['tickets_invalidos']}")
        print(f"🗑️  Tickets descartados: {stats['tickets_descartados']}")
        print(f"❌ Errores: {stats['errores']}")
        
        if stats['errores_detalle']:
            print("\\n📋 Detalle de errores:")
            for i, err in enumerate(stats['errores_detalle'][:5], 1):
                print(f"  {i}. {err}")
            
            if len(stats['errores_detalle']) > 5:
                print(f"  ... y {len(stats['errores_detalle']) - 5} errores más")
        
        print("="*60)
        
        logger.info(f"Resumen: {json.dumps(stats)}")