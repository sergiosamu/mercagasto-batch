# Configuración para Render PostgreSQL

Esta guía te ayudará a configurar el proyecto mercagasto-batch para usar una base de datos PostgreSQL en Render.

## 🎯 Configuración en Render

### 1. Crear Base de Datos PostgreSQL

1. Ve a tu dashboard de Render
2. Clic en "New" → "PostgreSQL"
3. Configura:
   - **Name**: `mercagasto-db` (o el nombre que prefieras)
   - **Database**: `mercagasto`
   - **User**: `mercagasto_user`
   - **Region**: Selecciona la más cercana
   - **PostgreSQL Version**: 15 o superior
   - **Plan**: Free (para desarrollo) o Starter (para producción)

4. Clic en "Create Database"

### 2. Obtener Credenciales

Después de crear la base de datos, Render te proporcionará:

```
Hostname: abcd-efgh-ijkl.oregon-postgres.render.com
Port: 5432
Database: mercagasto
Username: mercagasto_user
Password: [password generado]
```

**Importante**: Render también proporciona una `DATABASE_URL` completa que es la forma recomendada de conectar.

### 3. Configurar Variables de Entorno

En tu proyecto local, crea un archivo `.env` basado en `.env.render.example`:

```bash
# Copia el ejemplo
cp .env.render.example .env

# Edita con tus valores reales
nano .env
```

**Opción 1: Usar DATABASE_URL (Recomendado)**
```bash
DATABASE_URL=postgresql://usuario:password@host:puerto/database
```

**Opción 2: Variables individuales**
```bash
DB_HOST=abcd-efgh-ijkl.oregon-postgres.render.com
DB_PORT=5432
DB_NAME=mercagasto
DB_USER=mercagasto_user
DB_PASSWORD=tu_password_generado
DB_SSLMODE=require
```

## 🚀 Inicialización de la Base de Datos

### Paso 1: Configurar el Entorno Local

```bash
# Activar entorno virtual
source .venv/bin/activate

# Verificar configuración
echo $DATABASE_URL
```

### Paso 2: Ejecutar Script de Inicialización

```bash
# Ejecutar inicialización
uv run python init_render_db.py

# O con Python estándar
python init_render_db.py
```

Este script:
- ✅ Verifica la conexión a Render PostgreSQL
- ✅ Crea todas las tablas necesarias
- ✅ Carga datos iniciales de categorías
- ✅ Configura índices y vistas
- ✅ Verifica que todo esté correcto

### Paso 3: Verificar la Configuración

```bash
# Verificar estado de la base de datos
uv run python -c "
from src.mercagasto.config.settings import get_database_config
from src.mercagasto.storage.postgresql import PostgreSQLTicketStorage

config = get_database_config()
print(f'Host: {config.host}')
print(f'Database: {config.database}')
print(f'SSL: {config.sslmode}')

storage = PostgreSQLTicketStorage(config)
with storage.get_connection() as conn:
    print('✅ Conexión exitosa')
"
```

## 🔧 Consideraciones Especiales para Render

### 1. SSL/TLS Obligatorio
Render PostgreSQL **requiere** conexiones SSL:
- El código ya está configurado para detectar Render y usar `sslmode=require`
- No necesitas configuración adicional

### 2. Timeouts de Conexión
- Render puede tener timeouts más estrictos
- El código incluye `connect_timeout=30` por defecto
- Monitorea los logs si hay problemas de timeout

### 3. Límites del Plan Free
- **Conexiones**: Máximo 97 conexiones concurrentes
- **Almacenamiento**: 1 GB
- **Retención**: 90 días
- **Backups**: Solo en planes pagos

### 4. Conexiones Desde Múltiples IPs
- Render PostgreSQL acepta conexiones desde cualquier IP
- Tu aplicación local puede conectarse directamente
- Considera usar IP whitelisting en producción

## 📊 Scripts Útiles

### Backup de Datos
```bash
# Exportar datos
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Importar datos
psql $DATABASE_URL < backup_20241207.sql
```

### Consultas de Monitoreo
```sql
-- Ver conexiones activas
SELECT count(*) FROM pg_stat_activity;

-- Ver tamaño de base de datos
SELECT pg_size_pretty(pg_database_size('mercagasto'));

-- Ver tablas con más datos
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE tablename IN ('tickets', 'productos', 'mercadona_productos');
```

## 🚨 Troubleshooting

### Error: "SSL connection required"
```bash
# Verificar que sslmode esté configurado
echo $DB_SSLMODE  # Debe ser 'require'

# O verificar DATABASE_URL
echo $DATABASE_URL  # Debe incluir ?sslmode=require
```

### Error: "Connection timeout"
```bash
# Verificar conectividad
ping abcd-efgh-ijkl.oregon-postgres.render.com

# Probar conexión directa
psql $DATABASE_URL -c "SELECT 1;"
```

### Error: "Too many connections"
```bash
# Ver conexiones activas
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Terminar conexiones ociosas (cuidado en producción)
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND query_start < now() - interval '5 minutes';
"
```

### Performance Lenta
1. Verificar índices:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename IN ('tickets', 'productos');
   ```

2. Analizar consultas:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM productos_categorized_view LIMIT 10;
   ```

3. Actualizar estadísticas:
   ```sql
   ANALYZE;
   ```

## 🔒 Seguridad

### Variables de Entorno en Render
Al desplegar en Render, configura las variables de entorno en el dashboard:

1. Ve a tu servicio en Render
2. Settings → Environment Variables
3. Añade:
   - `DATABASE_URL`: (automático con la BD)
   - `GMAIL_CREDENTIALS`: archivo base64 o JSON
   - `LOG_LEVEL`: INFO
   - `ENVIRONMENT`: production

### Credenciales de Gmail
Para Gmail API en Render, considera:

1. **Opción 1**: Subir `credentials.json` como variable de entorno
2. **Opción 2**: Usar Google Cloud Service Account
3. **Opción 3**: Configurar OAuth2 específico para producción

## 📈 Migración desde Local

### 1. Exportar Datos Locales
```bash
# Exportar desde PostgreSQL local
pg_dump -h localhost -U postgres mercadona > export_local.sql
```

### 2. Importar a Render
```bash
# Importar a Render
psql $DATABASE_URL < export_local.sql
```

### 3. Verificar Migración
```bash
# Ejecutar verificaciones
uv run python init_render_db.py
```

## 🎉 ¡Listo!

Tu aplicación mercagasto-batch ahora está configurada para usar Render PostgreSQL. El sistema automáticamente detectará si está ejecutándose en local o conectado a Render y ajustará la configuración SSL apropiadamente.