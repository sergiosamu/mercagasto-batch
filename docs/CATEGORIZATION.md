# Sistema de Categorización de Productos

Este documento describe el sistema de categorización automática de productos implementado en mercagasto-batch.

## 🎯 Objetivo

Asociar automáticamente productos extraídos de tickets de Mercadona con categorías predefinidas para generar reportes de gastos organizados por tipo de producto.

## 🏗️ Arquitectura del Sistema

### 1. Base de Datos

**Tablas principales:**
- `categorias`: Categorías principales (ej. "Alimentación", "Higiene")
- `subcategorias`: Subcategorías específicas (ej. "Lácteos", "Carnes")
- `mercadona_productos`: Catálogo completo de productos de Mercadona
- `productos`: Productos extraídos de tickets con referencias a categorías

**Vistas de reporting:**
- `productos_categorized_view`: Vista consolidada de productos con categorías
- `gastos_por_categoria`: Resumen de gastos agrupados por categoría

### 2. Componentes del Sistema

#### a) Extractor de Catálogo (`mercadona_api_client.py`)
- **Propósito**: Extraer productos del catálogo online de Mercadona
- **Funcionalidad**: 
  - Navega por categorías de la web de Mercadona
  - Extrae información completa de productos (nombre, precio, categoría)
  - Maneja paginación y rate limiting
- **Salida**: Productos estructurados para carga en BD

#### b) Cargador de Productos (`product_loader.py`)
- **Propósito**: Cargar datos del catálogo en la base de datos
- **Funcionalidad**:
  - Procesa archivos JSON del scraper
  - Realiza UPSERT para evitar duplicados
  - Valida y normaliza datos de productos
- **Características**: Manejo robusto de errores y logging detallado

#### c) Motor de Matching (`product_matcher.py`)
- **Propósito**: Asociar productos de tickets con categorías
- **Algoritmos de matching**:
  1. **Exact Match**: Coincidencia exacta por nombre
  2. **Fuzzy Match**: Matching por similitud usando difflib
  3. **Keyword Match**: Búsqueda por palabras clave
  4. **Price-based Match**: Matching por precio cuando hay múltiples candidatos

## 🔄 Flujo de Trabajo

### 1. Preparación Inicial

```bash
# 1. Cargar categorías desde JSON
uv run python load_categories.py

# 2. Extraer catálogo de productos
uv run python scrape_mercadona.py

# 3. Cargar productos en BD
uv run python product_loader.py productos_mercadona.json
```

### 2. Procesamiento de Tickets

```bash
# Procesar tickets y categorizar productos
uv run python categorize_products.py

# O usar el proceso completo
uv run python extract_and_load.py
```

### 3. Consultas de Ejemplo

```sql
-- Ver productos categorizados
SELECT * FROM productos_categorized_view 
WHERE fecha >= '2024-01-01';

-- Gastos por categoría
SELECT categoria, SUM(precio_total) as total_gastado
FROM gastos_por_categoria 
GROUP BY categoria 
ORDER BY total_gastado DESC;

-- Productos sin categorizar
SELECT * FROM productos 
WHERE categoria_id IS NULL;
```

## 📊 Métricas de Matching

El sistema de matching proporciona métricas de confianza:

- **Confidence Score**: 0.0-1.0 basado en calidad del match
- **Match Type**: Tipo de algoritmo usado
- **Match Details**: Información adicional del proceso

### Umbrales de Confianza

- `>= 0.9`: Match de alta confianza (automático)
- `0.7-0.9`: Match de confianza media (revisión opcional)
- `< 0.7`: Match de baja confianza (requiere revisión manual)

## 🔧 Scripts de CLI

### `categorize_products.py`
```bash
# Categorizar todos los productos sin categoría
uv run python categorize_products.py

# Categorizar productos específicos
uv run python categorize_products.py --ticket-id 123

# Modo verbose para debugging
uv run python categorize_products.py --verbose
```

### `extract_and_load.py`
```bash
# Proceso completo: scraping + carga + categorización
uv run python extract_and_load.py

# Con número específico de tiendas
uv run python extract_and_load.py --max-stores 50
```

### `scrape_mercadona.py`
```bash
# Extraer catálogo completo
uv run python scrape_mercadona.py

# Extraer solo categorías específicas
uv run python scrape_mercadona.py --categories "frescos,conservas"
```

## 📈 Monitoreo y Debugging

### Logging
Todos los componentes usan logging estructurado:
```python
# Configuración en config/logging.py
logger = setup_logger(__name__)
logger.info("Producto categorizado", extra={
    'producto_id': producto.id,
    'categoria': categoria.nombre,
    'confidence': match_result.confidence
})
```

### Estadísticas de Matching
```python
# Ver estadísticas de categorización
stats = matcher.get_categorization_stats()
print(f"Productos categorizados: {stats['categorized']}")
print(f"Sin categorizar: {stats['uncategorized']}")
print(f"Confianza promedio: {stats['avg_confidence']:.2f}")
```

## 🚀 Mejoras Futuras

1. **Machine Learning**: Implementar modelos de ML para matching más inteligente
2. **Auto-learning**: Sistema que aprende de correcciones manuales
3. **API REST**: Interfaz web para gestión de categorías
4. **Análisis predictivo**: Predicción de gastos basada en patrones históricos

## 📝 Troubleshooting

### Problemas Comunes

**Error: "No se pudo categorizar producto"**
- Verificar que el catálogo esté actualizado
- Revisar si el producto existe en `mercadona_productos`
- Considerar ajustar umbrales de matching

**Baja tasa de matching**
- Actualizar catálogo de productos
- Revisar calidad de extracción de texto de tickets
- Ajustar algoritmos de fuzzy matching

**Performance lenta**
- Verificar índices en base de datos
- Considerar batch processing para grandes volúmenes
- Optimizar queries de matching