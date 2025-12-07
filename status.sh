#!/bin/bash
# Script para mostrar el estado del proyecto mercagasto-batch con uv

echo "📊 Estado del proyecto mercagasto-batch"
echo "====================================="
echo ""

echo "🐍 Entorno Python:"
echo "  Versión: $(python3 --version)"
echo "  Intérprete: $(which python3)"
echo ""

echo "📦 Gestión de dependencias:"
echo "  Herramienta: uv $(uv --version)"
echo "  Archivo lock: $(if [ -f uv.lock ]; then echo '✅ uv.lock'; else echo '❌ Sin uv.lock'; fi)"
echo "  Entorno virtual: $(if [ -d .venv ]; then echo '✅ .venv/'; else echo '❌ Sin .venv/'; fi)"
echo ""

echo "📋 Paquetes instalados (principales):"
echo "  $(uv pip list | grep -E "(mercagasto|psycopg2|pdfplumber|google-api|requests)" | wc -l) paquetes principales"
echo ""

echo "🛠️  Herramientas de desarrollo:"
echo "  $(uv pip list | grep -E "(pytest|black|flake8|mypy|pre-commit)" | wc -l) herramientas disponibles"
echo ""

echo "🚀 Scripts de CLI disponibles:"
for script in categorize_products.py extract_and_load.py load_categories.py scrape_mercadona.py; do
    if [ -f "$script" ]; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script (no encontrado)"
    fi
done
echo ""

echo "🎯 Comandos útiles:"
echo "=================="
echo "Activar entorno:"
echo "  source .venv/bin/activate"
echo ""
echo "Ejecutar con uv:"
echo "  uv run python categorize_products.py --help"
echo "  uv run pytest"
echo "  uv run black ."
echo "  uv run flake8 ."
echo ""
echo "Gestión de dependencias:"
echo "  uv add <paquete>        # Añadir dependencia"
echo "  uv remove <paquete>     # Eliminar dependencia"
echo "  uv sync                 # Sincronizar entorno"
echo "  uv lock                 # Actualizar lock file"
echo ""

echo "✅ ¡Proyecto configurado y listo para usar!"