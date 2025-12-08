"""
Utilidad completa para debuggear el procesamiento de PDFs de Mercadona.

Este script te permite:
1. Ver el texto extraído del PDF
2. Ver cómo se parsea el texto a objetos de aplicación
3. Validar la consistencia de los datos
4. Ver problemas específicos de parsing

Uso:
  python debug_pdf_processing.py <archivo.pdf>
  python debug_pdf_processing.py <directorio_con_pdfs>
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from mercagasto.processors.pdf_extractor import PDFTextExtractor
from mercagasto.parsers.mercadona import MercadonaTicketParser
from mercagasto.models.ticket import TicketData, Product

def print_separator(title: str, char: str = "=", width: int = 80):
    """Imprime un separador decorativo."""
    print()
    print(char * width)
    print(f" {title} ".center(width, char))
    print(char * width)

def print_subsection(title: str):
    """Imprime un subtítulo."""
    print(f"\n📌 {title}")
    print("-" * (len(title) + 4))

def format_price(price):
    """Formatea precio para mostrar."""
    if price is None:
        return "N/A"
    return f"{price:.2f}€"

def debug_pdf(pdf_path: Path):
    """Debuggea un PDF específico."""
    
    print_separator(f"DEBUGGING: {pdf_path.name}")
    
    # 1. Extracción de texto
    print_subsection("1. EXTRACCIÓN DE TEXTO DEL PDF")
    
    try:
        text = PDFTextExtractor.extract_text_from_pdf(str(pdf_path))
        if not text:
            print("❌ No se pudo extraer texto del PDF")
            return
        
        print(f"✅ Texto extraído: {len(text)} caracteres")
        print("-" * 40)
        print(text)
        print("-" * 40)
        
        # Mostrar líneas para debug
        lines = text.split('\n')
        print(f"\n📝 Estructura del texto ({len(lines)} líneas):")
        for i, line in enumerate(lines, 1):  # Primeras 20 líneas
            print(f"{i:2d}: {repr(line)}")
            
    except Exception as e:
        print(f"❌ Error extrayendo texto: {e}")
        return
    
    # 2. Parsing del texto
    print_subsection("2. PARSING DEL TEXTO")
    
    try:
        parser = MercadonaTicketParser(text)
        ticket = parser.parse()
        
        print(f"✅ Ticket parseado exitosamente")
        print(f"📊 Información básica:")
        print(f"   🏪 Tienda: {ticket.store_name}")
        print(f"   📍 Dirección: {ticket.address}")
        print(f"   📍 Ciudad: {ticket.city}")
        print(f"   📞 Teléfono: {ticket.phone}")
        print(f"   🆔 CIF: {ticket.cif}")
        print(f"   📄 Nº Factura: {ticket.invoice_number}")
        print(f"   📅 Fecha: {ticket.date}")
        print(f"   🕐 Hora: {ticket.time}")
        print(f"   💳 Pago: {ticket.payment_method}")
        print(f"   💰 Total: {format_price(ticket.total)}")
        
    except Exception as e:
        print(f"❌ Error parseando texto: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Análisis de productos
    print_subsection("3. PRODUCTOS ENCONTRADOS")
    
    if not ticket.products:
        print("❌ No se encontraron productos")
    else:
        print(f"✅ {len(ticket.products)} productos encontrados:")
        
        total_calculado = 0.0
        
        for i, product in enumerate(ticket.products, 1):
            print(f"\n  {i:2d}. {product.description}")
            print(f"      Cantidad: {product.quantity}")
            print(f"      Precio unitario: {format_price(product.unit_price)}")
            print(f"      Precio total: {format_price(product.total_price)}")
            print(f"      Peso: {product.weight or 'N/A'}")
            
            if product.total_price:
                total_calculado += product.total_price
        
        print(f"\n📊 Resumen de productos:")
        print(f"   📦 Total productos: {len(ticket.products)}")
        print(f"   💰 Suma calculada: {format_price(total_calculado)}")
        print(f"   💰 Total del ticket: {format_price(ticket.total)}")
        
        diferencia = abs(total_calculado - ticket.total) if ticket.total else 0
        if diferencia > 0.01:
            print(f"   ⚠️  Diferencia: {format_price(diferencia)}")
        else:
            print(f"   ✅ Totales coinciden")
    
    # 4. Análisis del IVA
    print_subsection("4. DESGLOSE DE IVA")
    
    if not ticket.iva_breakdown:
        print("ℹ️  No hay información de IVA")
    else:
        print("📊 Desglose encontrado:")
        total_iva = 0.0
        for tipo_iva, datos in ticket.iva_breakdown.items():
            base = datos.get('base', 0)
            cuota = datos.get('cuota', 0)
            print(f"   {tipo_iva}: Base {format_price(base)} + IVA {format_price(cuota)}")
            total_iva += cuota
        
        print(f"   💰 Total IVA: {format_price(total_iva)}")
    
    # 5. Validación
    print_subsection("5. VALIDACIÓN")
    
    # Importar storage para validar
    try:
        from mercagasto.storage.postgresql import PostgreSQLTicketStorage
        from mercagasto.config.settings import get_database_config
        
        # Solo validamos, no guardamos
        db_config = get_database_config()
        storage = PostgreSQLTicketStorage(db_config)
        is_valid, errors = storage.validate_ticket(ticket)
        
        if is_valid:
            print("✅ Ticket válido para guardar en BD. Lo guardamos")
            ticket_id = storage.save_ticket(ticket)
            print(f"📝 Ticket guardado con ID: {ticket_id}")
            
            # Recuperar ticket guardado usando el ID correcto
            storedTicket = storage.get_ticket_by_id(ticket_id)
            print(f"🔍 Recuperando ticket ID: {ticket_id}")
            
            if storedTicket:
                print(f"✅ Ticket recuperado con {len(storedTicket.products)} productos")
                
                # Mostrar el ID del ticket (usar ticket_id directamente si storedTicket.id no existe)
                stored_id = getattr(storedTicket, 'id', ticket_id)
                print(f"🆔 ID del ticket guardado: {stored_id}")
                
                print(f"\n🔎 Comparando ticket guardado con el parseado:")
                mismatches = []
                
                # Comparar atributos básicos (excluyendo date y time)
                basic_attrs = [
                    "store_name", "cif", "address", "city", "phone",
                    "invoice_number", "total", "payment_method"
                ]
                for attr in basic_attrs:
                    pdf_value = getattr(ticket, attr, None)
                    db_value = getattr(storedTicket, attr, None)
                    if pdf_value != db_value:
                        mismatches.append(f"  - {attr}: PDF={pdf_value!r} | BD={db_value!r}")
                
                # Comparar fecha (solo año, mes, día - sin horas/minutos)
                pdf_date = getattr(ticket, 'date', None)
                db_date = getattr(storedTicket, 'date', None)
                if pdf_date and db_date:
                    # Convertir a fecha simple si son datetime
                    if hasattr(pdf_date, 'date'):
                        pdf_date = pdf_date.date()
                    if hasattr(db_date, 'date'):
                        db_date = db_date.date()
                    if pdf_date != db_date:
                        mismatches.append(f"  - date: PDF={pdf_date!r} | BD={db_date!r}")
                elif pdf_date != db_date:
                    mismatches.append(f"  - date: PDF={pdf_date!r} | BD={db_date!r}")
                
                # Comparar hora (solo hora:minuto - sin segundos)
                pdf_time = getattr(ticket, 'time', None)
                db_time = getattr(storedTicket, 'time', None)
                if pdf_time and db_time:
                    # Normalizar a string HH:MM
                    def normalize_time(t):
                        if hasattr(t, 'strftime'):
                            return t.strftime('%H:%M')
                        elif isinstance(t, str):
                            # Si es string, tomar solo HH:MM
                            return t[:5] if len(t) >= 5 else t
                        return str(t)
                    
                    pdf_time_norm = normalize_time(pdf_time)
                    db_time_norm = normalize_time(db_time)
                    
                    if pdf_time_norm != db_time_norm:
                        mismatches.append(f"  - time: PDF={pdf_time_norm!r} | BD={db_time_norm!r}")
                elif pdf_time != db_time:
                    mismatches.append(f"  - time: PDF={pdf_time!r} | BD={db_time!r}")

                # Comparar productos
                if len(ticket.products) != len(storedTicket.products):
                    mismatches.append(f"  - Número de productos: PDF={len(ticket.products)} | BD={len(storedTicket.products)}")
                else:
                    for i, (p_pdf, p_db) in enumerate(zip(ticket.products, storedTicket.products), 1):
                        for field in ["description", "quantity", "unit_price", "total_price", "weight"]:
                            v_pdf = getattr(p_pdf, field, None)
                            v_db = getattr(p_db, field, None)
                            
                            # Función para normalizar valores None/0.0
                            def normalize_price_value(val):
                                if val is None or val == 0.0:
                                    return 0.0
                                return float(val)
                            
                            # Para precios, comparar con tolerancia mínima y normalización
                            if field in ["unit_price", "total_price"]:
                                v_pdf_norm = normalize_price_value(v_pdf)
                                v_db_norm = normalize_price_value(v_db)
                                
                                if abs(v_pdf_norm - v_db_norm) > 0.01:
                                    mismatches.append(f"  - Producto {i} {field}: PDF={v_pdf!r} | BD={v_db!r}")
                            elif v_pdf != v_db:
                                mismatches.append(f"  - Producto {i} {field}: PDF={v_pdf!r} | BD={v_db!r}")

                # Comparar desglose de IVA
                if ticket.iva_breakdown != storedTicket.iva_breakdown:
                    mismatches.append(f"  - iva_breakdown: PDF={ticket.iva_breakdown} | BD={storedTicket.iva_breakdown}")

                if not mismatches:
                    print("✅ Los datos del ticket guardado coinciden con los del PDF.")
                else:
                    print("⚠️  Diferencias encontradas entre el ticket parseado y el guardado:")
                    for m in mismatches:
                        print(m)
            else:
                print("⚠️  No se pudo recuperar el ticket guardado para comparar.")
            
        else:
            print("❌ Ticket inválido:")
            for error in errors:
                print(f"   - {error}")
                
    except Exception as e:
        print(f"⚠️  No se pudo validar con BD: {e}")
    
    # 6. JSON debug
    print_subsection("6. REPRESENTACIÓN JSON (para debug)")
    
    try:
        # Convertir a dict para JSON
        ticket_dict = {
            "store_name": ticket.store_name,
            "cif": ticket.cif,
            "address": ticket.address,
            "city": ticket.city,
            "phone": ticket.phone,
            "date": str(ticket.date),
            "time": str(ticket.time),
            "invoice_number": ticket.invoice_number,
            "total": ticket.total,
            "payment_method": ticket.payment_method,
            "products": [
                {
                    "description": p.description,
                    "quantity": p.quantity,
                    "unit_price": p.unit_price,
                    "total_price": p.total_price,
                    "weight": p.weight
                }
                for p in ticket.products
            ],
            "iva_breakdown": ticket.iva_breakdown
        }
        
        json_output = json.dumps(ticket_dict, indent=2, ensure_ascii=False)
        print("📄 JSON del ticket parseado:")
        print(json_output[:1000])  # Primeros 1000 caracteres
        if len(json_output) > 1000:
            print("\n... (JSON truncado, ver archivo completo)")
        
    except Exception as e:
        print(f"⚠️  Error generando JSON: {e}")

def main():
    """Función principal."""
    
    if len(sys.argv) != 2:
        print("Uso: python debug_pdf_processing.py <archivo.pdf|directorio>")
        print("\nEjemplos:")
        print("  python debug_pdf_processing.py ticket.pdf")
        print("  python debug_pdf_processing.py tests/data/pdfs/")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if not path.exists():
        print(f"❌ No existe: {path}")
        sys.exit(1)
    
    if path.is_file() and path.suffix.lower() == '.pdf':
        # Archivo PDF individual
        debug_pdf(path)
        
    elif path.is_dir():
        # Directorio con PDFs
        pdf_files = list(path.glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No se encontraron archivos PDF en: {path}")
            sys.exit(1)
        
        print(f"🔍 Encontrados {len(pdf_files)} archivos PDF")
        
        for pdf_file in sorted(pdf_files):
            debug_pdf(pdf_file)
            
            if len(pdf_files) > 1:
                input("\n⏸️  Presiona Enter para continuar con el siguiente archivo...")
    
    else:
        print(f"❌ Debe ser un archivo PDF o un directorio")
        sys.exit(1)
    
    print_separator("DEBUG COMPLETADO", "=")
    print("🎉 Análisis finalizado")

if __name__ == "__main__":
    main()