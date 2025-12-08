#!/usr/bin/env python3
"""
Script para debuggear específicamente la extracción del número de factura.
"""

import sys
import logging
import re
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_invoice_patterns():
    """Prueba diferentes patrones de número de factura."""
    import re
    
    # Ejemplos de texto que podrían aparecer en tickets
    test_texts = [
        "FACTURA SIMPLIFICADA: 123-456-789",
        "FACTURA: 987654321", 
        "Nº FACTURA: 555-666-777",
        "Nº FAC: 111-222-333",
        "INVOICE: 444-555-666",
        "123-456-789",
        "Mercadona S.A. 987-654-321",
        "OP: 12345 FACTURA SIMPLIFICADA: 999-888-777",
        "15/12/2024 16:30",
        "123456789",
        "FAC123456789",
        "Factura Nº: 888-999-000"
    ]
    
    patterns = [
        (r'FACTURA[^:]*:\s*(\d+[-\d]*)', 'FACTURA: número'),
        (r'(\d{3,}-\d+-\d+)', 'Patrón XXX-X-X'),
        (r'(\d{8,})', 'Número de 8+ dígitos'),
        (r'Nº[^:]*:\s*(\d+[-\d]*)', 'Nº: número'),
        (r'(\d+-\d+-\d+)', 'Patrón general X-X-X'),
        (r'FAC(\d+)', 'FAC seguido de números'),
    ]
    
    print("🧪 Probando patrones de número de factura")
    print("=" * 60)
    
    for text in test_texts:
        print(f"\n📄 Texto: '{text}'")
        
        found_any = False
        for pattern, description in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"   ✅ {description}: {matches}")
                found_any = True
        
        if not found_any:
            print("   ❌ No se encontraron patrones")

def create_test_file():
    """Crea un archivo de prueba con formato típico de Mercadona."""
    
    test_content = """MERCADONA S.A. A-46103834
Avda. de Francia, 11
46023 VALENCIA
Tel: 963 123 456

15/12/2024 16:30
OP: 56789

FACTURA SIMPLIFICADA: 123-456-789

Descripción                           Importe
====================================================
LECHE ENTERA 1L                       1.25
PAN DE MOLDE INTEGRAL                 2.10
TOMATES RAMA 500G                     1.85
ACEITE OLIVA VIRGEN 1L                4.50
====================================================

TOTAL                                 9.70€

EFECTIVO                              10.00€
CAMBIO                                0.30€

Gracias por su compra
"""
    
    test_file = Path("test_ticket.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"📄 Archivo de prueba creado: {test_file}")
    return test_file

def test_with_parser(file_path):
    """Prueba el parser con el archivo."""
    
    from mercagasto.parsers.mercadona import MercadonaTicketParser
    from mercagasto.config.logging import setup_logging, get_logger
    
    # Configurar logging para ver el debug
    setup_logging(log_level=logging.DEBUG)
    logger = get_logger("test_parser")
    
    print(f"\n🔍 Probando parser con: {file_path}")
    print("=" * 50)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print("📋 Contenido del archivo:")
    for i, line in enumerate(text.split('\n'), 1):
        print(f"  {i:2d}: {line}")
    
    print(f"\n🚀 Ejecutando parser...")
    
    try:
        parser = MercadonaTicketParser(text)
        
        # Buscar número de factura directamente en las líneas
        invoice_number = None
        
        print(f"\n🔍 Buscando número de factura línea por línea:")
        for i, line in enumerate(parser.lines, 1):
            clean_line = parser._clean_text(line)
            print(f"   {i:2d}: '{clean_line}'")
            
            # Aplicar los mismos patrones del parser
            if "FACTURA SIMPLIFICADA:" in clean_line:
                match = re.search(r'(\d+-\d+-\d+)', clean_line)
                if match:
                    invoice_number = match.group(1)
                    print(f"       ✅ ENCONTRADO con patrón 'FACTURA SIMPLIFICADA': {invoice_number}")
            elif "FACTURA:" in clean_line:
                match = re.search(r'FACTURA:\s*(\d+)', clean_line)
                if match:
                    invoice_number = match.group(1) 
                    print(f"       ✅ ENCONTRADO con patrón 'FACTURA:': {invoice_number}")
            elif re.search(r'Nº\s*(?:FACTURA|FAC):', clean_line, re.IGNORECASE):
                match = re.search(r'(\d+-\d+-\d+|\d+)', clean_line)
                if match:
                    invoice_number = match.group(1)
                    print(f"       ✅ ENCONTRADO con patrón 'Nº FACTURA': {invoice_number}")
                    
        print(f"\n✅ RESULTADO FINAL:")
        print(f"   Número de factura encontrado: '{invoice_number}'")
        
        if invoice_number:
            print(f"\n🎉 ¡Número de factura extraído correctamente!")
        else:
            print(f"\n❌ No se pudo extraer el número de factura")
            print(f"   Verifica que el formato del PDF sea correcto")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_with_parser_text(text):
    """Prueba el parser con texto directo."""
    
    from mercagasto.parsers.mercadona import MercadonaTicketParser
    from mercagasto.config.logging import setup_logging, get_logger
    
    # Configurar logging para ver el debug
    setup_logging(log_level=logging.DEBUG)
    logger = get_logger("test_parser")
    
    print(f"\n🔍 Analizando texto extraído")
    print("=" * 50)
    
    print("📋 Primeras 10 líneas del contenido:")
    lines = text.split('\n')
    for i, line in enumerate(lines[:10], 1):
        print(f"  {i:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
    
    if len(lines) > 10:
        print(f"  ... (total {len(lines)} líneas)")
    
    print(f"\n🚀 Ejecutando parser...")
    
    try:
        parser = MercadonaTicketParser(text)
        
        # Buscar número de factura directamente en las líneas
        invoice_number = None
        
        print(f"\n🔍 Buscando número de factura línea por línea:")
        for i, line in enumerate(parser.lines, 1):
            clean_line = parser._clean_text(line)
            
            # Mostrar solo líneas que puedan contener info relevante
            if any(keyword in clean_line.upper() for keyword in ['FACTURA', 'FAC', 'OP:', 'MERCADONA', 'TOTAL']):
                print(f"   {i:2d}: '{clean_line}'")
            
            # Aplicar los mismos patrones del parser
            if "FACTURA SIMPLIFICADA:" in clean_line:
                match = re.search(r'(\d+-\d+-\d+)', clean_line)
                if match:
                    invoice_number = match.group(1)
                    print(f"       ✅ ENCONTRADO con patrón 'FACTURA SIMPLIFICADA': {invoice_number}")
            elif "FACTURA:" in clean_line:
                match = re.search(r'FACTURA:\s*(\d+)', clean_line)
                if match:
                    invoice_number = match.group(1) 
                    print(f"       ✅ ENCONTRADO con patrón 'FACTURA:': {invoice_number}")
            elif re.search(r'Nº\s*(?:FACTURA|FAC):', clean_line, re.IGNORECASE):
                match = re.search(r'(\d+-\d+-\d+|\d+)', clean_line)
                if match:
                    invoice_number = match.group(1)
                    print(f"       ✅ ENCONTRADO con patrón 'Nº FACTURA': {invoice_number}")
                    
        print(f"\n✅ RESULTADO FINAL:")
        print(f"   Número de factura encontrado: '{invoice_number}'")
        
        if invoice_number:
            print(f"\n🎉 ¡Número de factura extraído correctamente!")
        else:
            print(f"\n❌ No se pudo extraer el número de factura")
            print(f"   Verifica que el formato del PDF sea correcto")
            
            # Mostrar todas las líneas para debug
            print(f"\n🔍 Mostrando todas las líneas para debug:")
            for i, line in enumerate(parser.lines[:20], 1):  # Primeras 20 líneas
                clean_line = parser._clean_text(line)
                print(f"   {i:2d}: '{clean_line}'")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔧 Debug de extracción de número de factura")
    print("=" * 50)
    
    # Verificar si se pasó un archivo como argumento
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        
        if not file_path.exists():
            print(f"❌ El archivo {file_path} no existe")
            sys.exit(1)
            
        print(f"📄 Procesando archivo: {file_path}")
        
        if file_path.suffix.lower() == '.pdf':
            # Procesar PDF
            from mercagasto.processors.pdf_extractor import PDFTextExtractor
            
            try:
                text = PDFTextExtractor.extract_text_from_pdf(str(file_path))
                if text:
                    print(f"✅ Texto extraído del PDF ({len(text)} caracteres)")
                else:
                    print(f"❌ No se pudo extraer texto del PDF")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ Error extrayendo texto del PDF: {e}")
                sys.exit(1)
        else:
            # Leer archivo de texto
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                print(f"✅ Archivo de texto leído ({len(text)} caracteres)")
            except Exception as e:
                print(f"❌ Error leyendo archivo: {e}")
                sys.exit(1)
        
        # Probar con el parser
        test_with_parser_text(text)
        
    else:
        # Ejecutar pruebas de patrones
        test_invoice_patterns()
        
        # Crear archivo de prueba
        test_file = create_test_file()
        
        # Probar con el parser
        test_with_parser(test_file)
        
        print(f"\n💡 Para probar con tu propio archivo:")
        print(f"   uv run python test_invoice_debug.py tu_archivo.pdf")