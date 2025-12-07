"""
Utilidad para generar archivos de resultados esperados a partir de PDFs.

Ejecuta este script para procesar PDFs y generar los JSON esperados automáticamente.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Añadir src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mercagasto.parsers import MercadonaTicketParser
from mercagasto.processors import PDFTextExtractor


def serialize_ticket_data(ticket):
    """Convierte TicketData a diccionario serializable."""
    result = {
        'store_name': ticket.store_name,
        'cif': ticket.cif,
        'address': ticket.address,
        'postal_code': ticket.postal_code,
        'city': ticket.city,
        'phone': ticket.phone,
        'date': ticket.date.strftime('%Y-%m-%d') if ticket.date else None,
        'time': ticket.time,
        'order_number': ticket.order_number,
        'invoice_number': ticket.invoice_number,
        'total': ticket.total,
        'payment_method': ticket.payment_method,
        'products': [],
        'iva_breakdown': ticket.iva_breakdown
    }
    
    # Serializar productos
    for product in ticket.products:
        result['products'].append({
            'quantity': product.quantity,
            'description': product.description,
            'unit_price': product.unit_price,
            'total_price': product.total_price,
            'weight': product.weight
        })
    
    return result


def generate_expected_results():
    """Genera archivos JSON esperados para todos los PDFs en tests/data/pdfs/."""
    
    # Directorios
    test_dir = Path(__file__).parent
    pdfs_dir = test_dir / 'data' / 'pdfs'
    expected_dir = test_dir / 'data' / 'expected'
    
    # Crear directorio expected si no existe
    expected_dir.mkdir(exist_ok=True)
    
    # Verificar que existe directorio de PDFs
    if not pdfs_dir.exists():
        print(f"❌ Directorio {pdfs_dir} no existe")
        print(f"💡 Crea el directorio y coloca tus PDFs ahí")
        return
    
    # Buscar archivos PDF
    pdf_files = list(pdfs_dir.glob('*.pdf'))
    
    if not pdf_files:
        print(f"📁 No hay archivos PDF en {pdfs_dir}")
        print(f"💡 Coloca algunos tickets de Mercadona en PDF ahí")
        return
    
    print(f"🔍 Encontrados {len(pdf_files)} archivos PDF")
    print("="*50)
    
    extractor = PDFTextExtractor()
    
    for pdf_file in pdf_files:
        print(f"\n📄 Procesando: {pdf_file.name}")
        
        try:
            # Extraer texto
            text = extractor.extract_text_from_pdf(str(pdf_file))
            
            if not text:
                print(f"   ❌ No se pudo extraer texto")
                continue
                
            if len(text.strip()) < 100:
                print(f"   ⚠️  Texto extraído muy corto ({len(text)} chars)")
                continue
            
            print(f"   ✅ Texto extraído: {len(text)} caracteres")
            
            # Parsear ticket
            parser = MercadonaTicketParser(text)
            ticket = parser.parse()
            
            if not ticket.invoice_number:
                print(f"   ❌ No se pudo extraer número de factura")
                continue
                
            if ticket.total <= 0:
                print(f"   ❌ Total inválido: {ticket.total}")
                continue
                
            if not ticket.products:
                print(f"   ❌ No se encontraron productos")
                continue
            
            print(f"   ✅ Parseado: {ticket.invoice_number}, {ticket.total}€, {len(ticket.products)} productos")
            
            # Serializar y guardar
            result = serialize_ticket_data(ticket)
            
            json_name = pdf_file.name.replace('.pdf', '.json')
            json_file = expected_dir / json_name
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Guardado: {json_file.name}")
            
        except Exception as e:
            print(f"   ❌ Error procesando {pdf_file.name}: {e}")
            continue
    
    print("\n" + "="*50)
    print(f"✅ Generación completada")
    print(f"📂 Archivos JSON en: {expected_dir}")
    print(f"\n🧪 Ejecutar tests:")
    print(f"   pytest tests/test_integration.py -v")


def validate_existing_results():
    """Valida los resultados esperados existentes."""
    
    test_dir = Path(__file__).parent
    expected_dir = test_dir / 'data' / 'expected'
    
    if not expected_dir.exists():
        print("📁 No hay directorio de resultados esperados")
        return
    
    json_files = list(expected_dir.glob('*.json'))
    
    if not json_files:
        print("📁 No hay archivos JSON de resultados esperados")
        return
    
    print(f"🔍 Validando {len(json_files)} archivos JSON")
    print("="*50)
    
    for json_file in json_files:
        print(f"\n📄 Validando: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validaciones básicas
            required_fields = ['total', 'invoice_number', 'products']
            missing = [field for field in required_fields if field not in data]
            
            if missing:
                print(f"   ❌ Campos faltantes: {missing}")
                continue
            
            if data['total'] <= 0:
                print(f"   ❌ Total inválido: {data['total']}")
                continue
            
            if not data['products']:
                print(f"   ❌ Sin productos")
                continue
            
            print(f"   ✅ Válido: {data['invoice_number']}, {data['total']}€, {len(data['products'])} productos")
            
        except Exception as e:
            print(f"   ❌ Error validando {json_file.name}: {e}")
    
    print("\n" + "="*50)
    print(f"✅ Validación completada")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de resultados esperados para tests')
    parser.add_argument('--validate', action='store_true', help='Validar resultados existentes')
    parser.add_argument('--generate', action='store_true', help='Generar nuevos resultados')
    
    args = parser.parse_args()
    
    if args.validate:
        validate_existing_results()
    elif args.generate:
        generate_expected_results()
    else:
        print("🛠️  Generador de Resultados Esperados")
        print()
        print("Opciones:")
        print("  --generate    Generar JSONs esperados desde PDFs")
        print("  --validate    Validar JSONs existentes")
        print()
        print("Ejemplos:")
        print("  python tests/generate_expected.py --generate")
        print("  python tests/generate_expected.py --validate")