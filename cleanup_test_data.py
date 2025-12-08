#!/usr/bin/env python3
"""
Script para limpiar datos de test de la base de datos.

Este script permite:
1. Ver los tickets de prueba existentes
2. Limpiar tickets específicos por ID
3. Limpiar todos los tickets de un período determinado
4. Limpiar solo tickets con facturas que contengan ciertos patrones

Uso:
    uv run python cleanup_test_data.py --list                    # Ver tickets existentes
    uv run python cleanup_test_data.py --ids 1,2,3              # Limpiar tickets específicos
    uv run python cleanup_test_data.py --all-today              # Limpiar tickets de hoy
    uv run python cleanup_test_data.py --pattern "3274-*"       # Limpiar por patrón de factura
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.mercagasto.config.settings import get_database_config
from src.mercagasto.storage.postgresql import PostgreSQLTicketStorage


def list_tickets(storage):
    """Lista todos los tickets existentes."""
    
    try:
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        t.id, 
                        t.numero_factura, 
                        t.fecha_compra, 
                        t.total, 
                        COUNT(p.id) as num_productos,
                        t.created_at
                    FROM tickets t
                    LEFT JOIN productos p ON t.id = p.ticket_id
                    GROUP BY t.id, t.numero_factura, t.fecha_compra, t.total, t.created_at
                    ORDER BY t.created_at DESC
                    LIMIT 50
                """)
                
                tickets = cursor.fetchall()
                
                if not tickets:
                    print("📭 No hay tickets en la base de datos")
                    return []
                
                print(f"\\n📋 Tickets encontrados ({len(tickets)} de máximo 50):")
                print(f"{'ID':<6} {'Factura':<20} {'Fecha':<12} {'Total':<10} {'Productos':<10} {'Creado':<20}")
                print("-" * 80)
                
                for ticket in tickets:
                    tid, factura, fecha, total, productos, creado = ticket
                    fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
                    creado_str = creado.strftime('%Y-%m-%d %H:%M') if creado else 'N/A'
                    print(f"{tid:<6} {factura:<20} {fecha_str:<12} {total:<10.2f} {productos:<10} {creado_str:<20}")
                
                return [t[0] for t in tickets]  # Retornar solo IDs
                
    except Exception as e:
        print(f"❌ Error listando tickets: {e}")
        return []


def delete_tickets_by_ids(storage, ticket_ids):
    """Elimina tickets específicos por ID."""
    
    if not ticket_ids:
        print("⚠️  No se proporcionaron IDs válidos")
        return
    
    print(f"\\n🗑️  Eliminando {len(ticket_ids)} tickets...")
    
    deleted_count = 0
    for ticket_id in ticket_ids:
        try:
            success = storage.delete_ticket_by_id(ticket_id)
            if success:
                print(f"   ✅ Ticket {ticket_id} eliminado")
                deleted_count += 1
            else:
                print(f"   ⚠️  Ticket {ticket_id} no encontrado")
        except Exception as e:
            print(f"   ❌ Error eliminando ticket {ticket_id}: {e}")
    
    print(f"\\n📊 Resultado: {deleted_count}/{len(ticket_ids)} tickets eliminados")


def delete_tickets_by_pattern(storage, pattern):
    """Elimina tickets que coincidan con un patrón de número de factura."""
    
    try:
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                # Buscar tickets que coincidan con el patrón
                cursor.execute("""
                    SELECT id, numero_factura, fecha_compra, total
                    FROM tickets 
                    WHERE numero_factura LIKE %s
                    ORDER BY id
                """, (pattern.replace('*', '%'),))
                
                matching_tickets = cursor.fetchall()
                
                if not matching_tickets:
                    print(f"📭 No se encontraron tickets que coincidan con '{pattern}'")
                    return
                
                print(f"\\n🎯 Encontrados {len(matching_tickets)} tickets que coinciden con '{pattern}':")
                for ticket in matching_tickets:
                    tid, factura, fecha, total = ticket
                    fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
                    print(f"   {tid}: {factura} ({fecha_str}, {total}€)")
                
                # Confirmar eliminación
                response = input(f"\\n❓ ¿Eliminar estos {len(matching_tickets)} tickets? (y/N): ")
                if response.lower() not in ['y', 'yes', 's', 'sí']:
                    print("🚫 Operación cancelada")
                    return
                
                # Eliminar tickets
                ticket_ids = [t[0] for t in matching_tickets]
                delete_tickets_by_ids(storage, ticket_ids)
                
    except Exception as e:
        print(f"❌ Error buscando tickets por patrón: {e}")


def delete_todays_tickets(storage):
    """Elimina todos los tickets creados hoy."""
    
    today = date.today()
    
    try:
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                # Buscar tickets de hoy
                cursor.execute("""
                    SELECT id, numero_factura, total
                    FROM tickets 
                    WHERE DATE(created_at) = %s
                    ORDER BY id
                """, (today,))
                
                todays_tickets = cursor.fetchall()
                
                if not todays_tickets:
                    print(f"📭 No hay tickets creados hoy ({today})")
                    return
                
                print(f"\\n📅 Encontrados {len(todays_tickets)} tickets creados hoy ({today}):")
                for ticket in todays_tickets:
                    tid, factura, total = ticket
                    print(f"   {tid}: {factura} ({total}€)")
                
                # Confirmar eliminación
                response = input(f"\\n❓ ¿Eliminar todos los tickets de hoy? (y/N): ")
                if response.lower() not in ['y', 'yes', 's', 'sí']:
                    print("🚫 Operación cancelada")
                    return
                
                # Eliminar tickets
                ticket_ids = [t[0] for t in todays_tickets]
                delete_tickets_by_ids(storage, ticket_ids)
                
    except Exception as e:
        print(f"❌ Error buscando tickets de hoy: {e}")


def main():
    parser = argparse.ArgumentParser(description="Limpiar datos de test de la base de datos")
    parser.add_argument('--list', action='store_true', 
                      help='Listar tickets existentes')
    parser.add_argument('--ids', type=str,
                      help='IDs de tickets a eliminar (separados por comas)')
    parser.add_argument('--all-today', action='store_true',
                      help='Eliminar todos los tickets creados hoy')
    parser.add_argument('--pattern', type=str,
                      help='Patrón de número de factura (usar * como wildcard)')
    
    args = parser.parse_args()
    
    if not any([args.list, args.ids, args.all_today, args.pattern]):
        parser.print_help()
        return
    
    print("🔌 Conectando a la base de datos...")
    try:
        db_config = get_database_config()
        storage = PostgreSQLTicketStorage(db_config)
        print("✅ Conexión establecida")
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return
    
    try:
        if args.list:
            list_tickets(storage)
        
        elif args.ids:
            try:
                ticket_ids = [int(x.strip()) for x in args.ids.split(',') if x.strip()]
                delete_tickets_by_ids(storage, ticket_ids)
            except ValueError:
                print("❌ IDs inválidos. Usa números separados por comas")
        
        elif args.all_today:
            delete_todays_tickets(storage)
        
        elif args.pattern:
            delete_tickets_by_pattern(storage, args.pattern)
    
    finally:
        storage.close()
        print("\\n🔌 Conexión cerrada")


if __name__ == '__main__':
    main()