#!/bin/bash
# Script de instalación y configuración de uv para el proyecto

set -e

echo "🚀 Configurando uv para el proyecto mercagasto-batch"
echo "=================================================="

# Verificar si uv está instalado
if ! command -v uv &> /dev/null; then
    echo "❌ uv no está instalado. Instalando uv..."
    
    # Instalar uv usando el instalador oficial
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Añadir uv al PATH para esta sesión
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verificar instalación
    if command -v uv &> /dev/null; then
        echo "✅ uv instalado correctamente"
        uv --version
    else
        echo "❌ Error instalando uv"
        exit 1
    fi
else
    echo "✅ uv ya está instalado"
    uv --version
fi

echo ""
echo "📦 Inicializando proyecto con uv..."

# Eliminar requirements.txt si existe (será reemplazado por pyproject.toml)
if [ -f "requirements.txt" ]; then
    echo "📝 Respaldando requirements.txt como requirements.txt.bak"
    mv requirements.txt requirements.txt.bak
fi

# Eliminar uv.lock.placeholder
if [ -f "uv.lock.placeholder" ]; then
    rm uv.lock.placeholder
fi

echo ""
echo "🔧 Configurando entorno virtual..."

# Crear entorno virtual con uv
uv venv

echo ""
echo "📥 Instalando dependencias principales..."

# Instalar dependencias principales
uv pip install -e .

echo ""
echo "🛠️  Instalando dependencias de desarrollo..."

# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"

echo ""
echo "📊 Estado del proyecto:"
echo "====================="

# Mostrar información del entorno
echo "🐍 Python:"
uv python --version

echo ""
echo "📦 Paquetes instalados:"
uv pip list

echo ""
echo "✅ Configuración de uv completada!"
echo ""
echo "🎯 Próximos pasos:"
echo "=================="
echo "1. Activar el entorno virtual:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Verificar que todo funciona:"
echo "   python -c \"import mercagasto; print('✅ Importación exitosa')\""
echo ""
echo "3. Ejecutar tests:"
echo "   uv run pytest"
echo ""
echo "4. Comandos útiles de uv:"
echo "   uv pip install <paquete>     # Instalar paquete"
echo "   uv pip list                  # Listar paquetes"
echo "   uv pip sync                  # Sincronizar dependencias"
echo "   uv run <comando>             # Ejecutar comando en el entorno"
echo ""
echo "📚 Para más información: https://docs.astral.sh/uv/"