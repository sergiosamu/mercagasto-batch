"""
Almacenamiento en PostgreSQL para tickets.
"""

import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any, Union
import traceback

from .base import TicketStorageBase
from ..models import TicketData, ProcessingStatus, Product
from ..config import get_logger, DatabaseConfig

logger = get_logger(__name__)


class PostgreSQLTicketStorage(TicketStorageBase):
    """Implementación de almacenamiento en PostgreSQL."""
    
    def __init__(self, config: DatabaseConfig, debug_queries: bool = False):
        """
        Inicializa el almacenamiento PostgreSQL.
        
        Args:
            config: Configuración de la base de datos
            debug_queries: Si True, logea todas las consultas SQL
        """
        self.connection_params = {
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'user': config.user,
            'password': config.password,
            'sslmode': config.sslmode,
            'connect_timeout': config.connect_timeout,
            'application_name': config.application_name
        }
        self.debug_queries = debug_queries
        logger.info(f"Configurado almacenamiento PostgreSQL: {config.host}:{config.port}/{config.database} (SSL: {config.sslmode})")
        if debug_queries:
            logger.info("🔍 DEBUG de consultas SQL activado")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la BD."""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción de BD: {e}")
            raise e
        finally:
            conn.close()
    
    def create_tables(self) -> None:
        """Crea las tablas necesarias en PostgreSQL."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de tiendas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tiendas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(200) NOT NULL,
                    cif VARCHAR(20) UNIQUE NOT NULL,
                    direccion TEXT,
                    codigo_postal VARCHAR(10),
                    ciudad VARCHAR(100),
                    telefono VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    tienda_id INTEGER REFERENCES tiendas(id),
                    numero_pedido VARCHAR(50),
                    numero_factura VARCHAR(50) UNIQUE,
                    fecha_compra DATE NOT NULL,
                    hora_compra TIME NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    metodo_pago VARCHAR(50),
                    iva_4_base DECIMAL(10,2),
                    iva_4_cuota DECIMAL(10,2),
                    iva_10_base DECIMAL(10,2),
                    iva_10_cuota DECIMAL(10,2),
                    iva_21_base DECIMAL(10,2),
                    iva_21_cuota DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de productos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
                    cantidad INTEGER NOT NULL,
                    descripcion VARCHAR(200) NOT NULL,
                    precio_unitario DECIMAL(10,2),
                    precio_total DECIMAL(10,2) NOT NULL,
                    peso VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de tracking de procesamiento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_log (
                    id SERIAL PRIMARY KEY,
                    gmail_message_id VARCHAR(100) UNIQUE NOT NULL,
                    pdf_filename VARCHAR(500),
                    pdf_hash VARCHAR(64),
                    status VARCHAR(20) NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    last_attempt TIMESTAMP,
                    error_stage VARCHAR(50),
                    error_message TEXT,
                    error_traceback TEXT,
                    pdf_path TEXT,
                    extracted_text_path TEXT,
                    ticket_id INTEGER REFERENCES tickets(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata JSONB
                )
            """)
            
            # Tabla de backups de archivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_backups (
                    id SERIAL PRIMARY KEY,
                    processing_log_id INTEGER REFERENCES processing_log(id),
                    file_type VARCHAR(20) NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash VARCHAR(64),
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self._create_indexes(cursor)
            
            logger.info("✓ Tablas creadas exitosamente")
    
    def _create_indexes(self, cursor) -> None:
        """Crea índices para mejorar el rendimiento."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tickets_fecha ON tickets(fecha_compra)",
            "CREATE INDEX IF NOT EXISTS idx_productos_ticket ON productos(ticket_id)",
            "CREATE INDEX IF NOT EXISTS idx_productos_descripcion ON productos(descripcion)",
            "CREATE INDEX IF NOT EXISTS idx_processing_status ON processing_log(status)",
            "CREATE INDEX IF NOT EXISTS idx_processing_message_id ON processing_log(gmail_message_id)",
        ]
        
        for index in indexes:
            cursor.execute(index)
    
    def start_processing(self, message_id: str, pdf_filename: str, 
                        pdf_hash: str, pdf_path: str) -> int:
        """
        Registra el inicio del procesamiento de un ticket.
        
        Returns:
            ID del registro de procesamiento
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO processing_log (
                    gmail_message_id, pdf_filename, pdf_hash, status, 
                    attempts, last_attempt, pdf_path
                )
                VALUES (%s, %s, %s, %s, 1, NOW(), %s)
                ON CONFLICT (gmail_message_id) DO UPDATE SET
                    attempts = processing_log.attempts + 1,
                    last_attempt = NOW(),
                    status = EXCLUDED.status
                RETURNING id
            """, (message_id, pdf_filename, pdf_hash, 
                  ProcessingStatus.PENDING.value, pdf_path))
            
            result = cursor.fetchone()
            processing_id = result[0] if result else None
            if processing_id is None:
                raise ValueError("No se pudo obtener el ID del procesamiento")
            logger.info(f"Iniciado procesamiento ID: {processing_id} para mensaje {message_id}")
            return processing_id
    
    def update_processing_status(self, processing_id: int, status: ProcessingStatus,
                                error_stage: Optional[str] = None, error_message: Optional[str] = None,
                                error_traceback: Optional[str] = None, ticket_id: Optional[int] = None,
                                extracted_text_path: Optional[str] = None) -> None:
        """Actualiza el estado de procesamiento."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            completed_at = datetime.now() if status == ProcessingStatus.COMPLETED else None
            
            cursor.execute("""
                UPDATE processing_log
                SET status = %s,
                    error_stage = %s,
                    error_message = %s,
                    error_traceback = %s,
                    ticket_id = %s,
                    extracted_text_path = %s,
                    completed_at = %s
                WHERE id = %s
            """, (status.value, error_stage, error_message, error_traceback,
                  ticket_id, extracted_text_path, completed_at, processing_id))
            
            logger.debug(f"Actualizado procesamiento {processing_id} a estado: {status.value}")
    
    def get_failed_processings(self, max_attempts: int = 3) -> List[Dict[str, Any]]:
        """Obtiene procesamiento fallidos para reintentar."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, gmail_message_id, pdf_filename, pdf_path, 
                       attempts, error_message
                FROM processing_log
                WHERE status IN (%s, %s)
                AND attempts < %s
                ORDER BY last_attempt DESC
            """, (ProcessingStatus.FAILED.value, ProcessingStatus.RETRY.value, max_attempts))
            
            # Convertir a diccionario usando nombres de columna
            columns = [desc[0] for desc in cursor.description]
            return [
                {
                    'id': row[columns.index('id')],
                    'message_id': row[columns.index('gmail_message_id')],
                    'pdf_filename': row[columns.index('pdf_filename')],
                    'pdf_path': row[columns.index('pdf_path')],
                    'attempts': row[columns.index('attempts')],
                    'error_message': row[columns.index('error_message')]
                }
                for row in cursor.fetchall()
            ]
    
    def register_file_backup(self, processing_id: int, file_type: str,
                            file_path: str, file_hash: str, file_size: int) -> None:
        """Registra un backup de archivo."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO file_backups (
                    processing_log_id, file_type, file_path, 
                    file_hash, file_size
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (processing_id, file_type, file_path, file_hash, file_size))
            
            logger.debug(f"Registrado backup: {file_type} - {file_path}")
    
    def validate_ticket(self, ticket: TicketData) -> Tuple[bool, List[str]]:
        """Valida un ticket antes de guardarlo."""
        errors = []
        
        # Validaciones básicas
        if not ticket.total or ticket.total <= 0:
            errors.append("Total inválido o cero")
        
        if not ticket.products or len(ticket.products) == 0:
            errors.append("Sin productos")
        
        if not ticket.date:
            errors.append("Sin fecha")
        
        if not ticket.invoice_number:
            errors.append("Sin número de factura")
        
        # Validar que la suma de productos coincida exactamente con el total
        if not ticket.is_total_consistent:
            suma_productos = ticket.products_total
            errors.append(
                f"Suma de productos ({suma_productos:.2f}€) no coincide con total ({ticket.total:.2f}€)"
            )
        
        # Validar productos individualmente
        for i, p in enumerate(ticket.products):
            if not p.description:
                errors.append(f"Producto {i+1} sin descripción")
            if p.total_price <= 0:
                errors.append(f"Producto {i+1} con precio inválido")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Ticket no válido: {', '.join(errors)}")
        
        return is_valid, errors
    
    def save_ticket(self, ticket: TicketData) -> int:
        """Guarda un ticket completo en PostgreSQL."""
        # Validar ticket primero
        is_valid, errors = self.validate_ticket(ticket)
        if not is_valid:
            error_msg = f"Ticket inválido: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 1. Insertar o obtener tienda
                tienda_id = self._insert_or_get_store(cursor, ticket)
                
                # 2. Insertar ticket - IMPORTANTE: verificar si ya existe
                ticket_id, is_duplicate = self._insert_ticket(cursor, ticket, tienda_id)
                
                # 3. Solo insertar productos si NO es duplicado
                if not is_duplicate:
                    self._insert_products(cursor, ticket, ticket_id)
                    logger.info(f"✓ Ticket guardado - ID: {ticket_id}, Factura: {ticket.invoice_number}")
                else:
                    logger.warning(f"⚠️ Ticket duplicado detectado - ID: {ticket_id}, Factura: {ticket.invoice_number} - NO se insertaron productos")
                
                return ticket_id
                
            except Exception as e:
                logger.error(f"Error guardando ticket: {e}")
                logger.error(traceback.format_exc())
                raise
    
    def _insert_or_get_store(self, cursor, ticket: TicketData) -> int:
        """Inserta o obtiene la tienda."""
        cursor.execute("""
            INSERT INTO tiendas (nombre, cif, direccion, codigo_postal, ciudad, telefono)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (cif) DO UPDATE SET
                direccion = EXCLUDED.direccion,
                codigo_postal = EXCLUDED.codigo_postal,
                ciudad = EXCLUDED.ciudad,
                telefono = EXCLUDED.telefono
            RETURNING id
        """, (
            ticket.store_name, ticket.cif, ticket.address,
            ticket.postal_code, ticket.city, ticket.phone
        ))
        result = cursor.fetchone()
        if result is None:
            raise ValueError("No se pudo obtener el ID de la tienda")
        return result[0]
    
    def _insert_ticket(self, cursor, ticket: TicketData, tienda_id: int) -> Tuple[int, bool]:
        """
        Inserta el ticket principal.
        
        Returns:
            Tuple[int, bool]: (ticket_id, is_duplicate)
        """
        # Preparar datos de IVA con conversión de tipos segura
        iva_data: Dict[str, Dict[str, Optional[float]]] = {
            '4%': {'base': None, 'cuota': None},
            '10%': {'base': None, 'cuota': None},
            '21%': {'base': None, 'cuota': None}
        }
        
        # Actualizar con conversión segura de tipos
        for percentage, breakdown in ticket.iva_breakdown.items():
            if percentage in iva_data:
                iva_data[percentage] = {
                    'base': breakdown.get('base'),  # float → Optional[float]
                    'cuota': breakdown.get('cuota') # float → Optional[float]
                }
        
        cursor.execute("""
            INSERT INTO tickets (
                tienda_id, numero_pedido, numero_factura, fecha_compra, 
                hora_compra, total, metodo_pago,
                iva_4_base, iva_4_cuota,
                iva_10_base, iva_10_cuota,
                iva_21_base, iva_21_cuota
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (numero_factura) DO NOTHING
            RETURNING id
        """, (
            tienda_id, ticket.order_number, ticket.invoice_number,
            ticket.date, ticket.time, ticket.total, ticket.payment_method,
            iva_data['4%']['base'], iva_data['4%']['cuota'],
            iva_data['10%']['base'], iva_data['10%']['cuota'],
            iva_data['21%']['base'], iva_data['21%']['cuota']
        ))
        
        result = cursor.fetchone()
        if result is None:
            # El ticket ya existe (conflicto con numero_factura)
            cursor.execute("SELECT id FROM tickets WHERE numero_factura = %s", (ticket.invoice_number,))
            existing = cursor.fetchone()
            if existing is None:
                raise ValueError("No se pudo obtener el ticket duplicado")
            ticket_id = existing[0]
            logger.warning(f"Ticket duplicado detectado: factura {ticket.invoice_number}, ID {ticket_id}")
            return ticket_id, True  # ← is_duplicate = True
        
        return result[0], False  # ← is_duplicate = False
    
    def _insert_products(self, cursor, ticket: TicketData, ticket_id: int) -> None:
        """Inserta los productos del ticket."""
        productos_data = [
            (
                ticket_id, p.quantity, p.description,
                p.unit_price, p.total_price, p.weight
            )
            for p in ticket.products
        ]
        
        execute_values(cursor, """
            INSERT INTO productos (
                ticket_id, cantidad, descripcion, precio_unitario, 
                precio_total, peso
            )
            VALUES %s
        """, productos_data)
        
        logger.debug(f"Insertados {len(productos_data)} productos para ticket {ticket_id}")
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un ticket por su ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.id, t.numero_pedido, t.numero_factura,
                    t.fecha_compra, t.hora_compra, t.total, t.metodo_pago,
                    ti.nombre, ti.cif, ti.direccion, ti.ciudad
                FROM tickets t
                JOIN tiendas ti ON t.tienda_id = ti.id
                WHERE t.id = %s
            """, (ticket_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Convertir usando nombres de columna
            columns = [desc[0] for desc in cursor.description]
            ticket_dict = dict(zip(columns, row))
            
            # Obtener productos
            cursor.execute("""
                SELECT cantidad, descripcion, precio_unitario, precio_total, peso
                FROM productos
                WHERE ticket_id = %s
                ORDER BY id
            """, (ticket_id,))
            
            productos = cursor.fetchall()
            prod_columns = [desc[0] for desc in cursor.description]
            
            return {
                'id': ticket_dict['id'],
                'numero_pedido': ticket_dict['numero_pedido'],
                'numero_factura': ticket_dict['numero_factura'],
                'fecha': ticket_dict['fecha_compra'],
                'hora': ticket_dict['hora_compra'],
                'total': float(ticket_dict['total']),
                'metodo_pago': ticket_dict['metodo_pago'],
                'tienda': {
                    'nombre': ticket_dict['nombre'],
                    'cif': ticket_dict['cif'],
                    'direccion': ticket_dict['direccion'],
                    'ciudad': ticket_dict['ciudad']
                },
                'productos': [
                    dict(zip(prod_columns, p))
                    for p in productos
                ]
            }
    
    def get_tickets_by_date_range(self, fecha_inicio: str, fecha_fin: str) -> List[Dict[str, Any]]:
        """Obtiene tickets en un rango de fechas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, numero_factura, fecha_compra, total
                FROM tickets
                WHERE fecha_compra BETWEEN %s AND %s
                ORDER BY fecha_compra DESC
            """, (fecha_inicio, fecha_fin))
            
            columns = [desc[0] for desc in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
    
    def get_total_gastado(self, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None) -> float:
        """Calcula el total gastado en un periodo."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if fecha_inicio and fecha_fin:
                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0) as total_gastado
                    FROM tickets
                    WHERE fecha_compra BETWEEN %s AND %s
                """, (fecha_inicio, fecha_fin))
            else:
                cursor.execute("SELECT COALESCE(SUM(total), 0) as total_gastado FROM tickets")
            
            result = cursor.fetchone()
            return float(result[0]) if result else 0.0
    
    def get_productos_mas_comprados(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los productos más comprados."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    descripcion as producto,
                    COUNT(*) as veces_comprado,
                    SUM(cantidad) as cantidad_total,
                    ROUND(AVG(precio_total), 2) as precio_promedio,
                    ROUND(SUM(precio_total), 2) as gasto_total
                FROM productos
                GROUP BY descripcion
                ORDER BY veces_comprado DESC
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def test_connection(self) -> bool:
        """Test de conexión a la base de datos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Error en test de conexión: {e}")
            return False

    def get_ticket_by_id(self, ticket_id: int) -> Optional[TicketData]:
        """Obtiene un ticket por su ID."""
        if self.debug_queries:
            logger.info(f"🎯 get_ticket_by_id({ticket_id}) - INICIO")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Consultar ticket
            ticket_query = """
                SELECT 
                    t.id, t.tienda_id, t.numero_pedido, t.numero_factura,
                    t.fecha_compra, t.hora_compra, t.total, t.metodo_pago,
                    t.iva_4_base, t.iva_4_cuota,
                    t.iva_10_base, t.iva_10_cuota,
                    t.iva_21_base, t.iva_21_cuota,
                    ti.nombre as tienda_nombre, ti.cif, ti.direccion,
                    ti.codigo_postal, ti.ciudad, ti.telefono
                FROM tickets t
                LEFT JOIN tiendas ti ON t.tienda_id = ti.id
                WHERE t.id = %s
            """
            
            if self.debug_queries:
                logger.info(f"🔍 SQL [GET_TICKET]: {' '.join(ticket_query.split())}")
                logger.info(f"🔍 PARAMS: ({ticket_id},)")
            
            cursor.execute(ticket_query, (ticket_id,))
            row = cursor.fetchone()
            
            if not row:
                if self.debug_queries:
                    logger.info(f"❌ No se encontró ticket con ID {ticket_id}")
                return None
            
            # Convertir usando nombres de columna
            columns = [desc[0] for desc in cursor.description]
            ticket_dict = dict(zip(columns, row))
            
            if self.debug_queries:
                logger.info(f"✅ Ticket encontrado: {ticket_dict['numero_factura']}")
            
            # 2. Consultar productos
            products_query = """
                SELECT descripcion, cantidad, precio_unitario, precio_total, peso
                FROM productos
                WHERE ticket_id = %s
                ORDER BY id
            """
            
            if self.debug_queries:
                logger.info(f"🔍 SQL [GET_PRODUCTS]: {' '.join(products_query.split())}")
                logger.info(f"🔍 PARAMS: ({ticket_id},)")
            
            cursor.execute(products_query, (ticket_id,))
            product_rows = cursor.fetchall()
            
            if self.debug_queries:
                logger.info(f"📦 Productos encontrados: {len(product_rows)} para ticket {ticket_id}")
            
            products = []
            for i, prod_row in enumerate(product_rows):
                prod_columns = [desc[0] for desc in cursor.description]
                prod_dict = dict(zip(prod_columns, prod_row))
                
                if self.debug_queries and i < 3:  # Solo los primeros 3
                    logger.info(f"   📦 {i+1}: {prod_dict['descripcion']} - {prod_dict['cantidad']} x {prod_dict['precio_total']}€")
                
                product_data = Product(
                    quantity=prod_dict['cantidad'],
                    description=prod_dict['descripcion'],
                    unit_price=float(prod_dict['precio_unitario']) if prod_dict['precio_unitario'] else 0.0,
                    total_price=float(prod_dict['precio_total']),
                    weight=prod_dict.get('peso', '')
                )
                products.append(product_data)
            
            if self.debug_queries and len(product_rows) > 3:
                logger.info(f"   📦 ... y {len(product_rows) - 3} productos más")
            
            # Reconstruir desglose de IVA desde la BD
            iva_breakdown: Dict[str, Dict[str, float]] = {}
            
            # IVA 4%
            if ticket_dict.get('iva_4_base') or ticket_dict.get('iva_4_cuota'):
                iva_breakdown['4%'] = {
                    'base': float(ticket_dict['iva_4_base']) if ticket_dict['iva_4_base'] else 0.0,
                    'cuota': float(ticket_dict['iva_4_cuota']) if ticket_dict['iva_4_cuota'] else 0.0
                }
            
            # IVA 10%
            if ticket_dict.get('iva_10_base') or ticket_dict.get('iva_10_cuota'):
                iva_breakdown['10%'] = {
                    'base': float(ticket_dict['iva_10_base']) if ticket_dict['iva_10_base'] else 0.0,
                    'cuota': float(ticket_dict['iva_10_cuota']) if ticket_dict['iva_10_cuota'] else 0.0
                }
            
            # IVA 21%
            if ticket_dict.get('iva_21_base') or ticket_dict.get('iva_21_cuota'):
                iva_breakdown['21%'] = {
                    'base': float(ticket_dict['iva_21_base']) if ticket_dict['iva_21_base'] else 0.0,
                    'cuota': float(ticket_dict['iva_21_cuota']) if ticket_dict['iva_21_cuota'] else 0.0
                }
            
            # Crear TicketData desde BD con todos los campos requeridos
            ticket = TicketData(
                store_name=str(ticket_dict['tienda_nombre']) if ticket_dict['tienda_nombre'] else "Mercadona",
                cif=str(ticket_dict['cif']) if ticket_dict['cif'] else "A46103834",
                address=str(ticket_dict['direccion']) if ticket_dict['direccion'] else "",
                postal_code=str(ticket_dict['codigo_postal']) if ticket_dict['codigo_postal'] else "",
                city=str(ticket_dict['ciudad']) if ticket_dict['ciudad'] else "",
                phone=str(ticket_dict['telefono']) if ticket_dict['telefono'] else "",
                date=ticket_dict['fecha_compra'],
                time=str(ticket_dict['hora_compra']) if ticket_dict['hora_compra'] else "",
                order_number=str(ticket_dict['numero_pedido']) if ticket_dict['numero_pedido'] else "",
                invoice_number=str(ticket_dict['numero_factura']),
                products=products,
                total=float(ticket_dict['total']),
                payment_method=str(ticket_dict['metodo_pago']) if ticket_dict['metodo_pago'] else "",
                iva_breakdown=iva_breakdown
            )
            
            # Agregar el ID como atributo adicional
            setattr(ticket, 'id', ticket_dict['id'])
            
            if self.debug_queries:
                logger.info(f"🎯 get_ticket_by_id({ticket_id}) - FIN: {len(products)} productos creados")
            
            return ticket

    def get_ticket_by_invoice(self, invoice_number: str) -> Optional[TicketData]:
        """Obtiene un ticket por número de factura."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tickets WHERE numero_factura = %s", (invoice_number,))
            result = cursor.fetchone()
            
            if result:
                return self.get_ticket_by_id(result[0])
            return None

    def get_products_by_ticket_id(self, ticket_id: int) -> List[Product]:
        """Obtiene productos de un ticket específico."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT descripcion, cantidad, precio_unitario, precio_total, peso
                FROM productos
                WHERE ticket_id = %s
                ORDER BY id
            """, (ticket_id,))
            
            columns = [desc[0] for desc in cursor.description]
            products = []
            for row in cursor.fetchall():
                product_dict = dict(zip(columns, row))
                
                product = Product(
                    quantity=product_dict['cantidad'],
                    description=product_dict['descripcion'],
                    unit_price=float(product_dict['precio_unitario']) if product_dict['precio_unitario'] else 0.0,
                    total_price=float(product_dict['precio_total']),
                    weight=product_dict.get('peso', '')
                )
                products.append(product)
            
            return products

    def delete_test_tickets(self, ticket_ids: List[int]) -> None:
        """Elimina tickets de prueba (para limpieza en tests)."""
        if not ticket_ids:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar productos asociados (CASCADE debería hacerlo automáticamente)
            cursor.execute("""
                DELETE FROM productos 
                WHERE ticket_id = ANY(%s)
            """, (ticket_ids,))
            
            # Eliminar tickets
            cursor.execute("""
                DELETE FROM tickets 
                WHERE id = ANY(%s)
            """, (ticket_ids,))
            
            logger.info(f"Eliminados {len(ticket_ids)} tickets de prueba")

    def close(self) -> None:
        """Cierra la conexión (no necesario con context managers)."""
        # Los context managers manejan las conexiones automáticamente
        pass