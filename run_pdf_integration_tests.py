#!/usr/bin/env python3
"""
Script para ejecutar tests de integración con PDFs reales de Mercadona.

Este script:
1. Verifica la configuración de la base de datos
2. Crea el directorio de PDFs si no existe
3. Ejecuta los tests de integración enfocándose en PDFs reales
4. Proporciona instrucciones claras sobre cómo usar PDFs reales

Para usar:
1. Coloca tickets de Mercadona (en PDF) en tests/data/pdfs/
2. Ejecuta: uv run python run_pdf_integration_tests.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

import pytest


def check_setup():
    """Verifica la configuración antes de ejecutar tests."""
    
    print("🔍 Verificando configuración...")
    
    # Verificar directorio de PDFs
    pdfs_dir = Path(__file__).parent / 'tests' / 'data' / 'pdfs'
    pdf_files = list(pdfs_dir.glob('*.pdf')) if pdfs_dir.exists() else []
    
    if not pdfs_dir.exists():
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Creado directorio: {pdfs_dir}")
    
    print(f"📄 PDFs encontrados: {len(pdf_files)}")
    
    if not pdf_files:
        print(f"\\n⚠️  No hay archivos PDF en {pdfs_dir}")
        print(f"\\n💡 Para ejecutar tests completos:")
        print(f"   1. Consigue algunos tickets de Mercadona en formato PDF")
        print(f"   2. Colócalos en: {pdfs_dir}")
        print(f"   3. Ejecuta de nuevo este script")
        print(f"\\n📖 Los tests de configuración se ejecutarán igualmente...")
        return False
    else:
        print(f"\\n✅ Configuración lista con {len(pdf_files)} PDFs:")
        for pdf in pdf_files[:5]:  # Mostrar máximo 5
            print(f"   - {pdf.name}")
        if len(pdf_files) > 5:
            print(f"   ... y {len(pdf_files) - 5} más")
        return True


def run_pdf_tests():
    """Ejecuta los tests de integración para PDFs."""
    
    has_pdfs = check_setup()
    
    print(f"\\n🧪 Ejecutando tests de integración...")
    print(f"{'='*60}")
    
    # Configurar argumentos de pytest - desactivar configuración del proyecto
    pytest_args = [
        'tests/test_ticket_database_integration.py',
        '-v',
        '--tb=short',
        '-s',  # Mostrar prints
        '-o', 'addopts=',  # Sobreescribir addopts para evitar coverage
    ]
    
    if has_pdfs:
        # Si hay PDFs, ejecutar todos los tests
        print("🎯 Ejecutando tests completos con PDFs reales")
        pytest_args.extend([
            '-k', 'not simulation'  # Evitar tests de simulación
        ])
    else:
        # Si no hay PDFs, solo tests básicos
        print("🎯 Ejecutando tests básicos (sin PDFs reales)")
        pytest_args.extend([
            '-k', 'database_connection or pdf_directory_setup or has_real_pdfs_available or invalid_ticket_handling'
        ])
    
    # Ejecutar tests
    exit_code = pytest.main(pytest_args)
    
    print(f"\\n{'='*60}")
    if exit_code == 0:
        print("✅ Tests ejecutados exitosamente")
        if has_pdfs:
            print("🎉 PDFs procesados correctamente")
        else:
            print("💡 Para tests completos, agrega PDFs reales al directorio")
    else:
        print("❌ Algunos tests fallaron")
        if not has_pdfs:
            print("💡 Considera agregar PDFs reales para tests más completos")
    
    return exit_code == 0


if __name__ == '__main__':
    success = run_pdf_tests()
    
    if not success:
        print("\\n🔧 Tips de troubleshooting:")
        print("   - Verifica la configuración de la base de datos en .env")
        print("   - Asegúrate de que los PDFs son tickets válidos de Mercadona")
        print("   - Revisa los logs de error arriba para más detalles")
    
    exit(0 if success else 1)