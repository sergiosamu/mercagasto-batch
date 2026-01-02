"""
Aplicación principal del sistema de gestión de tickets de Mercadona.
"""

import argparse
import sys
from typing import Optional

from mercagasto.config import AppConfig, setup_logging, get_logger
from mercagasto.storage import PostgreSQLTicketStorage
from mercagasto.reports import EmailReporter
from mercagasto.processors import GmailTicketProcessor


def setup_application() -> tuple[AppConfig, PostgreSQLTicketStorage]:
    """Configura la aplicación."""
    # Cargar configuración
    config = AppConfig.from_env()
    
    # Configurar logging
    setup_logging(config.log_dir)
    logger = get_logger(__name__)
    
    logger.info("Iniciando sistema de gestión de tickets de Mercadona")
    
    # Configurar almacenamiento
    storage = PostgreSQLTicketStorage(config.database)
    
    try:
        # Crear tablas si no existen
        storage.create_tables()
    except Exception as e:
        logger.error(f"Error configurando base de datos: {e}")
        print(f"❌ Error conectando a la base de datos: {e}")
        print("💡 Verifica que PostgreSQL esté ejecutándose y la configuración sea correcta")
        sys.exit(1)
    
    return config, storage


def cmd_process_tickets(args):
    """Comando para procesar tickets desde Gmail."""
    logger = get_logger(__name__)
    
    config, storage = setup_application()
    
    print("🚀 Iniciando procesamiento de tickets desde Gmail...")
    
    # Crear procesador
    processor = GmailTicketProcessor(
        storage=storage,
        gmail_config=config.gmail,
        processing_config=config.processing
    )
    
    try:
        # Procesar tickets
        stats = processor.process_all_tickets(retry_failed=args.retry)
        
        # Mostrar resultado final
        print(f"\n✅ Procesamiento completado:")
        print(f"   📧 {stats['correos_encontrados']} correos procesados")
        print(f"   🎫 {stats['tickets_guardados']} tickets guardados")
        print(f"   🗑️ {stats['tickets_descartados']} tickets descartados")
        print(f"   ❌ {stats['errores']} errores")
        
        if stats['errores'] > 0:
            logger.warning(f"Se produjeron {stats['errores']} errores durante el procesamiento")
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {e}")
        print(f"❌ Error durante el procesamiento: {e}")
        sys.exit(1)


def cmd_send_weekly_report(args):
    """Comando para enviar reporte semanal."""
    logger = get_logger(__name__)
    
    config, storage = setup_application()
    
    print("📊 Generando y enviando reporte semanal...")
    
    # Crear reportero
    reporter = EmailReporter(storage, config.gmail)
    
    try:
        success = reporter.send_weekly_report(args.email)
        
        if success:
            print(f"✅ Reporte semanal enviado a {args.email}")
        else:
            print(f"❌ Error enviando reporte semanal")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error enviando reporte: {e}")
        print(f"❌ Error enviando reporte: {e}")
        sys.exit(1)


def cmd_send_monthly_report(args):
    """Comando para enviar reporte mensual."""
    logger = get_logger(__name__)
    
    config, storage = setup_application()
    
    print("📊 Generando y enviando reporte mensual...")
    
    # Crear reportero
    reporter = EmailReporter(storage, config.gmail)
    
    try:
        success = reporter.send_monthly_report(args.email)
        
        if success:
            print(f"✅ Reporte mensual enviado a {args.email}")
        else:
            print(f"❌ Error enviando reporte mensual")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error enviando reporte: {e}")
        print(f"❌ Error enviando reporte: {e}")
        sys.exit(1)


def cmd_setup_db(args):
    """Comando para configurar la base de datos."""
    logger = get_logger(__name__)
    
    print("🗄️  Configurando base de datos...")
    
    config, storage = setup_application()
    
    try:
        # Crear tablas
        storage.create_tables()
        print("✅ Base de datos configurada correctamente")
        
    except Exception as e:
        logger.error(f"Error configurando BD: {e}")
        print(f"❌ Error configurando base de datos: {e}")
        sys.exit(1)


def cmd_stats(args):
    """Comando para mostrar estadísticas."""
    logger = get_logger(__name__)
    
    config, storage = setup_application()
    
    print("📈 Estadísticas del sistema:")
    print("-" * 40)
    
    try:
        # Total gastado
        total = storage.get_total_gastado()
        print(f"💰 Total gastado: {total:.2f}€")
        
        # Top productos
        productos = storage.get_productos_mas_comprados(5)
        if productos:
            print(f"\n🏆 Top 5 productos más comprados:")
            for i, p in enumerate(productos, 1):
                print(f"   {i}. {p['producto']}: {p['gasto_total']:.2f}€ ({p['veces_comprado']} veces)")
        
        # Estadísticas de procesamiento si están disponibles
        if hasattr(storage, 'get_connection'):
            with storage.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tickets por estado
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM processing_log 
                    GROUP BY status 
                    ORDER BY COUNT(*) DESC
                """)
                
                print(f"\n📋 Estado de procesamiento:")
                for status, count in cursor.fetchall():
                    print(f"   {status}: {count}")
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        print(f"❌ Error obteniendo estadísticas: {e}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Sistema de gestión automática de tickets de Mercadona"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando para procesar tickets
    process_parser = subparsers.add_parser('process', help='Procesar tickets desde Gmail')
    process_parser.add_argument(
        '--no-retry', dest='retry', action='store_false',
        help='No reintentar tickets fallidos'
    )
    process_parser.set_defaults(func=cmd_process_tickets)
    
    # Comando para reporte semanal
    weekly_parser = subparsers.add_parser('weekly', help='Enviar reporte semanal')
    weekly_parser.add_argument('email', help='Email destinatario')
    weekly_parser.set_defaults(func=cmd_send_weekly_report)
    
    # Comando para reporte mensual
    monthly_parser = subparsers.add_parser('monthly', help='Enviar reporte mensual')
    monthly_parser.add_argument('email', help='Email destinatario')
    monthly_parser.set_defaults(func=cmd_send_monthly_report)
    
    # Comando para configurar BD
    setup_parser = subparsers.add_parser('setup-db', help='Configurar base de datos')
    setup_parser.set_defaults(func=cmd_setup_db)
    
    # Comando para estadísticas
    stats_parser = subparsers.add_parser('stats', help='Mostrar estadísticas')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Parsear argumentos
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ejecutar comando
    args.func(args)


if __name__ == '__main__':
    main()