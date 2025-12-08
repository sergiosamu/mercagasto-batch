#!/usr/bin/env python3
"""
Script para comparar cantidades extraídas vs esperadas
"""

import json
from src.mercagasto.parsers.mercadona import MercadonaTicketParser
from src.mercagasto.processors.pdf_extractor import PDFTextExtractor

def compare_quantities():
    # Cargar archivo esperado
    with open('tests/data/expected/20230918 Mercadona 75,22 €.json', 'r', encoding='utf-8') as f:
        expected = json.load(f)

    # Parsear PDF
    text = PDFTextExtractor.extract_text_from_pdf('tests/data/pdfs/20230918 Mercadona 75,22 €.pdf')
    ticket = MercadonaTicketParser(text).parse()

    print('🔍 Comparación de cantidades extraídas vs esperadas:')
    print('=' * 80)
    print(f'{"#":>2} | {"Descripción":30} | {"Qty Real":>8} | {"Qty Esperada":>12} | {"✓/✗":>5}')
    print('-' * 80)

    mismatches = 0
    for i, (actual, expected_prod) in enumerate(zip(ticket.products[:10], expected['products'][:10]), 1):
        match = '✅' if actual.quantity == expected_prod['quantity'] else '❌'
        if actual.quantity != expected_prod['quantity']:
            mismatches += 1
        print(f'{i:2d} | {actual.description[:30]:30} | {actual.quantity:8d} | {expected_prod["quantity"]:12d} | {match:>4}')

    print(f'\n📊 Resumen:')
    print(f'   • Total productos parseados: {len(ticket.products)}')
    print(f'   • Total productos esperados: {len(expected["products"])}')
    print(f'   • Coincide número de productos: {"✅" if len(ticket.products) == len(expected["products"]) else "❌"}')
    
    # Verificar que todas las cantidades coinciden
    all_quantities_match = all(
        actual.quantity == exp['quantity'] 
        for actual, exp in zip(ticket.products, expected['products'])
    )
    print(f'   • Todas las cantidades coinciden: {"✅" if all_quantities_match else "❌"}')
    print(f'   • Errores en cantidades (primeros 10): {mismatches}')
    
    # Mostrar estadísticas de cantidades
    actual_quantities = [p.quantity for p in ticket.products]
    expected_quantities = [p['quantity'] for p in expected['products']]
    
    print(f'\n📈 Estadísticas de cantidades:')
    print(f'   • Rango real: {min(actual_quantities)} - {max(actual_quantities)}')
    print(f'   • Rango esperado: {min(expected_quantities)} - {max(expected_quantities)}')
    print(f'   • Total unidades reales: {sum(actual_quantities)}')
    print(f'   • Total unidades esperadas: {sum(expected_quantities)}')

if __name__ == '__main__':
    compare_quantities()