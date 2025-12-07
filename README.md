# Sistema de Gestión de Tickets de Mercadona

Sistema automatizado para procesar tickets de compra de Mercadona desde Gmail, extraer información de productos y gastos, y generar reportes automáticos.

## 🚀 Características

- **Procesamiento automático de PDFs** desde Gmail
- **Extracción inteligente** de datos de tickets (productos, precios, fechas)
- **Almacenamiento seguro** en PostgreSQL con validación de datos
- **Control de duplicados** y manejo robusto de errores
- **Reportes automáticos** semanales y mensuales por email
- **Backup automático** de archivos procesados
- **Logging completo** de todas las operaciones

## 📁 Estructura del Proyecto

```
mercagasto-batch/
├── src/mercagasto/           # Código fuente principal
│   ├── config/               # Configuración y logging
│   ├── models/               # Modelos de datos
│   ├── parsers/              # Parsers de tickets
│   ├── storage/              # Almacenamiento en BD
│   ├── reports/              # Generación de reportes
│   └── processors/           # Procesamiento de Gmail
├── tests/                    # Tests unitarios
├── docs/                     # Documentación
├── main.py                   # Punto de entrada principal
├── requirements.txt          # Dependencias
├── .env.example              # Ejemplo de configuración
└── README.md                 # Este archivo
```

## 🛠️ Instalación

### Opción A: Instalación automática con uv (Recomendado)

1. **Ejecutar script de configuración**:
   ```bash
   git clone <repository-url>
   cd mercagasto-batch
   ./setup_uv.sh
   ```

### Opción B: Instalación manual con uv

1. **Instalar uv** (si no está instalado):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Base de Datos

**Desarrollo Local:**
- PostgreSQL local (ver configuración abajo)

**Producción:**
- Render PostgreSQL (ver [RENDER_SETUP.md](docs/RENDER_SETUP.md))
- Configuración automática con `DATABASE_URL`

2. **Configurar proyecto**:
   ```bash
   git clone <repository-url>
   cd mercagasto-batch
   uv venv
   uv pip install -e .
   uv pip install -e ".[dev]"  # Dependencias de desarrollo
   ```

### Opción C: Instalación tradicional con pip

1. **Crear entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -e .
   pip install -e ".[dev]"  # Dependencias de desarrollo
   ```

4. **Configurar base de datos PostgreSQL**:
   - Instalar PostgreSQL
   - Crear base de datos `mercadona`
   - Configurar credenciales

5. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

6. **Configurar Gmail API**:
   - Crear proyecto en Google Cloud Console
   - Habilitar Gmail API
   - Descargar `credentials.json`

## 📋 Configuración

### Variables de Entorno

Configura el archivo `.env` con tus valores:

```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mercadona
DB_USER=postgres
DB_PASSWORD=tu_password

# Gmail
GMAIL_CREDENTIALS=credentials.json
GMAIL_TOKEN=token.pickle

# Procesamiento
BACKUP_DIR=ticket_backups
MAX_RETRIES=3
```

### Gmail API

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto o seleccionar existente
3. Habilitar Gmail API
4. Crear credenciales OAuth 2.0
5. Descargar `credentials.json` al directorio raíz

## 🚀 Uso

### Con uv (Recomendado)

```bash
# Activar entorno virtual
source .venv/bin/activate

# Configurar base de datos (primera vez)
uv run python main.py setup-db

# Procesar tickets desde Gmail
uv run python main.py process

# Procesar sin reintentar fallidos
uv run python main.py process --no-retry

# Enviar reporte semanal
uv run python main.py weekly usuario@email.com

# Enviar reporte mensual
uv run python main.py monthly usuario@email.com

# Ver estadísticas
uv run python main.py stats

# Scripts adicionales
uv run python categorize_products.py --help
uv run python extract_and_load.py --help
```

### Con pip tradicional

```bash
# Activar entorno virtual
source .venv/bin/activate

# Configurar base de datos (primera vez)
python main.py setup-db

# Procesar tickets desde Gmail
python main.py process

# Ver estadísticas
python main.py stats
```

### Herramientas de desarrollo

```bash
# Ejecutar tests
uv run pytest

# Formatear código
uv run black .

# Verificar estilo de código
uv run flake8 .

# Verificar tipos
uv run mypy src/
```

### Gestión de dependencias con uv

```bash
# Añadir nueva dependencia
uv add <paquete>

# Añadir dependencia de desarrollo
uv add --dev <paquete>

# Eliminar dependencia
uv remove <paquete>

# Sincronizar entorno con el lock file
uv sync

# Actualizar dependencias
uv lock --upgrade

# Ver estado del proyecto
./status.sh
```

### Flujo de Trabajo Típico

1. **Configuración inicial**:
   ```bash
   python main.py setup-db
   ```

2. **Procesamiento regular** (ej. cron job):
   ```bash
   python main.py process
   ```

3. **Reportes automáticos**:
   ```bash
   # Semanal (lunes)
   python main.py weekly mi@email.com
   
   # Mensual (día 1)
   python main.py monthly mi@email.com
   ```

## 🏗️ Arquitectura

### Modelos de Datos
- **TicketData**: Información completa del ticket
- **Product**: Datos de productos individuales
- **ProcessingStatus**: Estados de procesamiento

### Componentes Principales
- **GmailTicketProcessor**: Procesador principal
- **MercadonaTicketParser**: Parser de tickets
- **PostgreSQLTicketStorage**: Almacenamiento en BD
- **EmailReporter**: Generador de reportes

### Flujo de Procesamiento
1. Buscar correos en Gmail
2. Descargar PDFs adjuntos
3. Extraer texto con pdfplumber
4. Parsear datos del ticket
5. Validar información
6. Guardar en PostgreSQL
7. Generar reportes

## 🔧 Desarrollo

### Estructura Modular
- `config/`: Configuración y logging
- `models/`: Definición de modelos
- `parsers/`: Lógica de parsing
- `storage/`: Capa de persistencia
- `reports/`: Generación de reportes
- `processors/`: Procesamiento de archivos

### Añadir Nuevos Parsers
1. Heredar de `TicketParserBase`
2. Implementar métodos abstractos
3. Registrar en el procesador

### Tests
```bash
python -m pytest tests/
```

## 🔍 Monitoreo

### Logs
- `logs/tickets_YYYYMMDD.log`: Log general
- `logs/errors_YYYYMMDD.log`: Solo errores

### Estados de Procesamiento
- `pending`: En espera
- `extracting`: Extrayendo texto
- `parsing`: Parseando datos
- `validating`: Validando
- `saving`: Guardando
- `completed`: Completado
- `failed`: Falló
- `retry`: Para reintento

## 🚨 Solución de Problemas

### Error de Conexión a BD
```bash
# Verificar PostgreSQL
systemctl status postgresql

# Crear base de datos
createdb mercadona
```

### Error de Gmail API
- Verificar `credentials.json`
- Reautenticar: eliminar `token.pickle`
- Verificar permisos del proyecto

### PDFs No se Procesan
- Verificar formato del PDF
- Comprobar logs de extracción
- Revisar carpeta `failed/`

## 📊 Métricas

El sistema rastrea:
- Correos procesados
- Tickets guardados
- Errores por tipo
- Productos más comprados
- Gastos por período

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-feature`
3. Commit cambios: `git commit -m 'Añadir nueva feature'`
4. Push a la rama: `git push origin feature/nueva-feature`
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

## ✨ Características Futuras

- [ ] Dashboard web
- [ ] Soporte para más supermercados
- [ ] API REST
- [ ] Análisis predictivo de gastos
- [ ] Notificaciones push
- [ ] Integración con apps móviles