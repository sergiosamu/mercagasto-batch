#!/usr/bin/env python3
"""
Script de debug para probar la extracción de números de factura.

Uso:
  python debug_invoice.py <archivo_pdf>
  python debug_invoice.py <archivo_txt>
"""

import sys
import logging
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mercagasto.processors.pdf_extractor import PDFTextExtractor
from mercagasto.parsers.mercadona import MercadonaTicketParser
from mercagasto.config.logging import setup_logger

def debug_invoice_extraction(file_path: str):
    """Debug de extracción de número de factura."""
    
    # Configurar logging para debug
    logger = setup_logger("debug_invoice", level=logging.DEBUG)
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        return
    
    print(f"🔍 Analizando: {file_path.name}")
    print("=" * 50)
    
    # Extraer texto
    if file_path.suffix.lower() == '.pdf':
        extractor = PDFTextExtractor()
        text = extractor.extract_text_from_pdf(str(file_path))
    else:
        # Asumir que es un archivo de texto
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    if not text:
        print("❌ No se pudo extraer texto")
        return
    
    print(f"📄 Texto extraído: {len(text)} caracteres")
    print()
    
    # Mostrar las primeras líneas
    lines = text.split('\n')[:20]
    print("📋 Primeras 20 líneas:")
    for i, line in enumerate(lines, 1):
        print(f"  {i:2d}: {line.strip()}")
    print()
    
    # Intentar parsear
    try:
        parser = MercadonaTicketParser(text)
        ticket = parser.parse()
        
        print("✅ RESULTADO DEL PARSING:")
        print(f"   Número de factura: '{ticket.invoice_number}'")
        print(f"   Fecha: {ticket.date}")
        print(f"   Total: {ticket.total}€")
        print(f"   Productos: {len(ticket.products)}")
        print(f"   Tienda: {ticket.store_name}")
        
        if not ticket.invoice_number:
            print("\n❌ NO SE ENCONTRÓ NÚMERO DE FACTURA")
            print("💡 El debug logging debería mostrar más información arriba")
        
    except Exception as e:
        print(f"❌ Error parseando: {e}")
        import traceback
        traceback.print_exc()

def manual_invoice_search(file_path: str):
    """Búsqueda manual de patrones de factura."""
    import re
    
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.pdf':
        extractor = PDFTextExtractor()
        text = extractor.extract_text_from_pdf(str(file_path))
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    print("\n🔍 BÚSQUEDA MANUAL DE PATRONES:")
    print("=" * 50)
    
    lines = text.split('\n')
    
    patterns = [
        (r'FACTURA[^:]*:\s*(\d+[-\d]*)', 'FACTURA: número'),
        (r'(\d{3,}-\d+-\d+)', 'Patrón XXX-X-X'),
        (r'(\d{8,})', 'Número de 8+ dígitos'),
        (r'Nº[^:]*:\s*(\d+[-\d]*)', 'Nº: número'),
        (r'(\d+-\d+-\d+)', 'Patrón general X-X-X'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, description in patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                print(f"  Línea {i:2d} ({description}): {matches}")
                print(f"           Texto: {line.strip()}")
                print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python debug_invoice.py <archivo_pdf_o_txt>")
        print()
        print("Ejemplos:")
        print("  python debug_invoice.py ticket.pdf")
        print("  python debug_invoice.py ticket.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    debug_invoice_extraction(file_path)
    manual_invoice_search(file_path)