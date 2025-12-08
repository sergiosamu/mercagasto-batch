-- =============================================================================
-- MODELO DE DATOS PARA SISTEMA DE GESTIÓN DE TICKETS DE MERCADONA
-- =============================================================================
-- 
-- Este archivo contiene el DDL (Data Definition Language) completo para crear
-- la estructura de base de datos del sistema de gestión automática de tickets.
--
-- Versión: 1.0.0
-- Fecha: 2025-12-07
-- Base de datos: PostgreSQL
-- =============================================================================

-- Eliminar tablas existentes (en orden inverso por dependencias)
DROP TABLE IF EXISTS file_backups CASCADE;
DROP TABLE IF EXISTS processing_log CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS tiendas CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS mercadona_productos CASCADE;
DROP TABLE IF EXISTS subcategorias CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;

-- =============================================================================
-- TABLA: categorias
-- Descripción: Categorías principales de productos de Mercadona
-- =============================================================================
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    orden INTEGER NOT NULL,
    is_extended BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT nombre_no_vacio CHECK (length(trim(nombre)) > 0)
);

-- =============================================================================
-- TABLA: subcategorias
-- Descripción: Subcategorías de productos de Mercadona
-- =============================================================================
CREATE TABLE subcategorias (
    id INTEGER PRIMARY KEY,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    orden INTEGER NOT NULL,
    layout INTEGER NOT NULL DEFAULT 1,
    published BOOLEAN NOT NULL DEFAULT true,
    is_extended BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT nombre_no_vacio CHECK (length(trim(nombre)) > 0),
    CONSTRAINT layout_valido CHECK (layout > 0)
);

-- =============================================================================
-- TABLA: usuarios
-- Descripción: Usuarios del sistema para envío de reportes
-- =============================================================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    opt_in_confirmado BOOLEAN NOT NULL DEFAULT false,
    fecha_opt_in TIMESTAMP,
    token_confirmacion VARCHAR(64),
    preferencias_reporte JSONB DEFAULT '{"semanal": true, "mensual": true}',
    ultimo_reporte_enviado TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT email_valido CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT opt_in_consistente CHECK (
        (opt_in_confirmado = false) OR 
        (opt_in_confirmado = true AND fecha_opt_in IS NOT NULL)
    )
);

-- =============================================================================
-- TABLA: tiendas
-- Descripción: Almacena información de las tiendas de Mercadona
-- =============================================================================
CREATE TABLE tiendas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    cif VARCHAR(20) UNIQUE NOT NULL,
    direccion TEXT,
    codigo_postal VARCHAR(10),
    ciudad VARCHAR(100),
    telefono VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLA: tickets
-- Descripción: Almacena información principal de los tickets de compra
-- =============================================================================
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    tienda_id INTEGER NOT NULL REFERENCES tiendas(id),
    numero_pedido VARCHAR(50),
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    fecha_compra DATE NOT NULL,
    hora_compra TIME NOT NULL,
    total DECIMAL(10,2) NOT NULL CHECK (total > 0),
    metodo_pago VARCHAR(50),
    iva_4_base DECIMAL(10,2),
    iva_4_cuota DECIMAL(10,2),
    iva_10_base DECIMAL(10,2),
    iva_10_cuota DECIMAL(10,2),
    iva_21_base DECIMAL(10,2),
    iva_21_cuota DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLA: mercadona_productos
-- Descripción: Productos extraídos de la API de Mercadona
-- =============================================================================
CREATE TABLE mercadona_productos (
    id VARCHAR(20) PRIMARY KEY,
    slug VARCHAR(200) NOT NULL,
    display_name VARCHAR(300) NOT NULL,
    packaging VARCHAR(100),
    published BOOLEAN NOT NULL DEFAULT true,
    share_url TEXT,
    thumbnail TEXT,
    product_limit INTEGER,
    
    -- Información de precios
    unit_price DECIMAL(10,4),
    bulk_price DECIMAL(10,4),
    reference_price DECIMAL(10,4),
    previous_unit_price DECIMAL(10,4),
    price_decreased BOOLEAN NOT NULL DEFAULT false,
    tax_percentage DECIMAL(5,3),
    iva INTEGER,
    is_new BOOLEAN NOT NULL DEFAULT false,
    
    -- Información de tamaño y empaque
    unit_name VARCHAR(50),
    unit_size DECIMAL(10,4),
    size_format VARCHAR(20),
    reference_format VARCHAR(20),
    is_pack BOOLEAN NOT NULL DEFAULT false,
    pack_size DECIMAL(10,4),
    total_units INTEGER,
    drained_weight DECIMAL(10,4),
    
    -- Selectores y métodos de venta
    unit_selector BOOLEAN NOT NULL DEFAULT false,
    bunch_selector BOOLEAN NOT NULL DEFAULT false,
    selling_method INTEGER,
    min_bunch_amount DECIMAL(10,4),
    increment_bunch_amount DECIMAL(10,4),
    approx_size BOOLEAN NOT NULL DEFAULT false,
    
    -- Badges e información adicional
    badges JSONB,
    status VARCHAR(50),
    unavailable_from TIMESTAMP,
    unavailable_weekdays JSONB,
    api_categories JSONB,
    
    -- Información de contexto
    categoria_id INTEGER REFERENCES categorias(id),
    categoria_name VARCHAR(100),
    subcategoria_id INTEGER REFERENCES subcategorias(id),
    subcategoria_name VARCHAR(100),
    nested_category_id INTEGER,
    nested_category_name VARCHAR(100),
    
    -- Metadatos de extracción
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT display_name_no_vacio CHECK (length(trim(display_name)) > 0),
    CONSTRAINT precios_validos CHECK (
        (unit_price IS NULL OR unit_price >= 0) AND
        (bulk_price IS NULL OR bulk_price >= 0) AND
        (reference_price IS NULL OR reference_price >= 0)
    ),
    CONSTRAINT tamaños_validos CHECK (
        (unit_size IS NULL OR unit_size > 0) AND
        (pack_size IS NULL OR pack_size > 0) AND
        (total_units IS NULL OR total_units > 0)
    )
);

-- =============================================================================
-- TABLA: productos
-- Descripción: Almacena los productos individuales de cada ticket
-- =============================================================================
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    descripcion VARCHAR(200) NOT NULL,
    precio_unitario DECIMAL(10,2),
    precio_total DECIMAL(10,2) NOT NULL CHECK (precio_total > 0),
    peso VARCHAR(50),
    
    -- Asociación con catálogo de Mercadona
    mercadona_producto_id VARCHAR(20) REFERENCES mercadona_productos(id),
    categoria_id INTEGER REFERENCES categorias(id),
    subcategoria_id INTEGER REFERENCES subcategorias(id),
    categoria_detectada VARCHAR(100),
    subcategoria_detectada VARCHAR(100),
    confidence_score DECIMAL(3,2), -- Puntuación de confianza del matching (0-1)
    matching_method VARCHAR(50), -- Método usado para el matching
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLA: processing_log
-- Descripción: Registro de procesamiento de tickets para tracking y debugging
-- =============================================================================
CREATE TABLE processing_log (
    id SERIAL PRIMARY KEY,
    gmail_message_id VARCHAR(100) UNIQUE NOT NULL,
    pdf_filename VARCHAR(500),
    pdf_hash VARCHAR(64),
    status VARCHAR(20) NOT NULL CHECK (
        status IN (
            'pending', 'downloading', 'extracting', 'parsing', 
            'validating', 'saving', 'completed', 'failed', 'retry'
        )
    ),
    attempts INTEGER DEFAULT 0 CHECK (attempts >= 0),
    last_attempt TIMESTAMP,
    error_stage VARCHAR(50),
    error_message TEXT,
    error_traceback TEXT,
    pdf_path TEXT,
    extracted_text_path TEXT,
    ticket_id INTEGER REFERENCES tickets(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- =============================================================================
-- TABLA: file_backups
-- Descripción: Registro de archivos de backup para auditoría
-- =============================================================================
CREATE TABLE file_backups (
    id SERIAL PRIMARY KEY,
    processing_log_id INTEGER NOT NULL REFERENCES processing_log(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('pdf', 'text', 'image')),
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    file_size INTEGER CHECK (file_size >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS
-- =============================================================================

-- Índices en tickets
CREATE INDEX idx_tickets_fecha_compra ON tickets(fecha_compra);
CREATE INDEX idx_tickets_tienda ON tickets(tienda_id);
CREATE INDEX idx_tickets_total ON tickets(total);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);

-- Índices en mercadona_productos
CREATE INDEX idx_mercadona_productos_categoria ON mercadona_productos(categoria_id);
CREATE INDEX idx_mercadona_productos_subcategoria ON mercadona_productos(subcategoria_id);
CREATE INDEX idx_mercadona_productos_display_name ON mercadona_productos(display_name);
CREATE INDEX idx_mercadona_productos_unit_price ON mercadona_productos(unit_price);
CREATE INDEX idx_mercadona_productos_published ON mercadona_productos(published);
CREATE INDEX idx_mercadona_productos_price_decreased ON mercadona_productos(price_decreased);
CREATE INDEX idx_mercadona_productos_extraction_date ON mercadona_productos(extraction_date);
CREATE INDEX idx_mercadona_productos_slug ON mercadona_productos(slug);

-- Índices en productos
CREATE INDEX idx_productos_ticket ON productos(ticket_id);
CREATE INDEX idx_productos_descripcion ON productos(descripcion);
CREATE INDEX idx_productos_precio_total ON productos(precio_total);
CREATE INDEX idx_productos_mercadona_id ON productos(mercadona_producto_id);
CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_productos_subcategoria ON productos(subcategoria_id);
CREATE INDEX idx_productos_confidence ON productos(confidence_score);
CREATE INDEX idx_productos_matching_method ON productos(matching_method);

-- Índices en categorias
CREATE INDEX idx_categorias_nombre ON categorias(nombre);
CREATE INDEX idx_categorias_orden ON categorias(orden);

-- Índices en subcategorias
CREATE INDEX idx_subcategorias_categoria ON subcategorias(categoria_id);
CREATE INDEX idx_subcategorias_nombre ON subcategorias(nombre);
CREATE INDEX idx_subcategorias_orden ON subcategorias(orden);
CREATE INDEX idx_subcategorias_published ON subcategorias(published);

-- Índices en processing_log
CREATE INDEX idx_processing_status ON processing_log(status);
CREATE INDEX idx_processing_message_id ON processing_log(gmail_message_id);
CREATE INDEX idx_processing_attempts ON processing_log(attempts);
CREATE INDEX idx_processing_created_at ON processing_log(created_at);

-- Índices en file_backups
CREATE INDEX idx_file_backups_processing_id ON file_backups(processing_log_id);
CREATE INDEX idx_file_backups_type ON file_backups(file_type);

-- Índices en tiendas
CREATE INDEX idx_tiendas_cif ON tiendas(cif);
CREATE INDEX idx_tiendas_ciudad ON tiendas(ciudad);

-- Índices en usuarios
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);
CREATE INDEX idx_usuarios_opt_in ON usuarios(opt_in_confirmado);
CREATE INDEX idx_usuarios_token ON usuarios(token_confirmacion);

-- =============================================================================
-- TRIGGERS PARA TIMESTAMPS AUTOMÁTICOS
-- =============================================================================

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para tiendas
CREATE TRIGGER update_tiendas_updated_at 
    BEFORE UPDATE ON tiendas 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para tickets
CREATE TRIGGER update_tickets_updated_at 
    BEFORE UPDATE ON tickets 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para usuarios
CREATE TRIGGER update_usuarios_updated_at 
    BEFORE UPDATE ON usuarios 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para mercadona_productos
CREATE TRIGGER update_mercadona_productos_updated_at 
    BEFORE UPDATE ON mercadona_productos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para categorias
CREATE TRIGGER update_categorias_updated_at 
    BEFORE UPDATE ON categorias 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para subcategorias
CREATE TRIGGER update_subcategorias_updated_at 
    BEFORE UPDATE ON subcategorias 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VISTAS ÚTILES PARA CONSULTAS
-- =============================================================================

-- Vista: tickets_completos
-- Descripción: Tickets con información de tienda incluida
CREATE VIEW tickets_completos AS
SELECT 
    t.id,
    t.numero_factura,
    t.fecha_compra,
    t.hora_compra,
    t.total,
    t.metodo_pago,
    ti.nombre as tienda_nombre,
    ti.cif as tienda_cif,
    ti.direccion as tienda_direccion,
    ti.ciudad as tienda_ciudad,
    t.created_at
FROM tickets t
JOIN tiendas ti ON t.tienda_id = ti.id;

-- Vista: tickets_por_categoria
-- Descripción: Gastos agrupados por categoría de productos
CREATE VIEW tickets_por_categoria AS
SELECT 
    c.id as categoria_id,
    c.nombre as categoria_nombre,
    COUNT(DISTINCT p.ticket_id) as num_tickets,
    COUNT(p.id) as num_productos,
    SUM(p.cantidad) as cantidad_total,
    ROUND(SUM(p.precio_total), 2) as gasto_total,
    ROUND(AVG(p.precio_total), 2) as precio_promedio,
    ROUND(AVG(p.confidence_score), 2) as confidence_promedio,
    MIN(t.fecha_compra) as primera_compra,
    MAX(t.fecha_compra) as ultima_compra
FROM categorias c
JOIN productos p ON c.id = p.categoria_id
JOIN tickets t ON p.ticket_id = t.id
GROUP BY c.id, c.nombre, c.orden
ORDER BY gasto_total DESC;

-- Vista: tickets_por_subcategoria
-- Descripción: Gastos agrupados por subcategoría de productos
CREATE VIEW tickets_por_subcategoria AS
SELECT 
    sc.id as subcategoria_id,
    sc.nombre as subcategoria_nombre,
    c.id as categoria_id,
    c.nombre as categoria_nombre,
    COUNT(DISTINCT p.ticket_id) as num_tickets,
    COUNT(p.id) as num_productos,
    SUM(p.cantidad) as cantidad_total,
    ROUND(SUM(p.precio_total), 2) as gasto_total,
    ROUND(AVG(p.precio_total), 2) as precio_promedio,
    ROUND(AVG(p.confidence_score), 2) as confidence_promedio
FROM subcategorias sc
JOIN categorias c ON sc.categoria_id = c.id
JOIN productos p ON sc.id = p.subcategoria_id
JOIN tickets t ON p.ticket_id = t.id
GROUP BY sc.id, sc.nombre, c.id, c.nombre
ORDER BY gasto_total DESC;

-- Vista: productos_con_categorias
-- Descripción: Productos con información completa de categorías
CREATE VIEW productos_con_categorias AS
SELECT 
    p.*,
    t.fecha_compra,
    t.total as ticket_total,
    ti.nombre as tienda_nombre,
    c.nombre as categoria_nombre,
    c.orden as categoria_orden,
    sc.nombre as subcategoria_nombre,
    mp.display_name as mercadona_nombre,
    mp.unit_price as mercadona_precio,
    mp.thumbnail as mercadona_imagen
FROM productos p
JOIN tickets t ON p.ticket_id = t.id
JOIN tiendas ti ON t.tienda_id = ti.id
LEFT JOIN categorias c ON p.categoria_id = c.id
LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
LEFT JOIN mercadona_productos mp ON p.mercadona_producto_id = mp.id;

-- Vista: estadisticas_matching
-- Descripción: Estadísticas de calidad del matching de productos
CREATE VIEW estadisticas_matching AS
SELECT 
    matching_method,
    COUNT(*) as total_productos,
    COUNT(CASE WHEN categoria_id IS NOT NULL THEN 1 END) as con_categoria,
    COUNT(CASE WHEN mercadona_producto_id IS NOT NULL THEN 1 END) as con_producto_mercadona,
    ROUND(AVG(confidence_score), 3) as confidence_promedio,
    ROUND(MIN(confidence_score), 3) as confidence_minima,
    ROUND(MAX(confidence_score), 3) as confidence_maxima,
    ROUND(
        (COUNT(CASE WHEN categoria_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)), 
        2
    ) as porcentaje_categorizados
FROM productos
WHERE matching_method IS NOT NULL
GROUP BY matching_method
ORDER BY total_productos DESC;

-- Vista: productos_mercadona_completos
-- Descripción: Productos de Mercadona con información de categorías
CREATE VIEW productos_mercadona_completos AS
SELECT 
    mp.*,
    c.nombre as categoria_nombre,
    c.orden as categoria_orden,
    sc.nombre as subcategoria_nombre,
    sc.orden as subcategoria_orden,
    sc.layout as subcategoria_layout
FROM mercadona_productos mp
LEFT JOIN categorias c ON mp.categoria_id = c.id
LEFT JOIN subcategorias sc ON mp.subcategoria_id = sc.id;

-- Vista: resumen_productos_por_categoria
-- Descripción: Estadísticas de productos por categoría
CREATE VIEW resumen_productos_por_categoria AS
SELECT 
    c.id as categoria_id,
    c.nombre as categoria_nombre,
    COUNT(mp.id) as total_productos,
    COUNT(CASE WHEN mp.published = true THEN 1 END) as productos_publicados,
    COUNT(CASE WHEN mp.price_decreased = true THEN 1 END) as productos_en_oferta,
    ROUND(AVG(mp.unit_price), 2) as precio_medio,
    MIN(mp.unit_price) as precio_minimo,
    MAX(mp.unit_price) as precio_maximo,
    MAX(mp.extraction_date) as ultima_extraccion
FROM categorias c
LEFT JOIN mercadona_productos mp ON c.id = mp.categoria_id
GROUP BY c.id, c.nombre, c.orden
ORDER BY c.orden;

-- Vista: productos_ofertas
-- Descripción: Productos con precio reducido
CREATE VIEW productos_ofertas AS
SELECT 
    mp.id,
    mp.display_name,
    mp.unit_price,
    mp.previous_unit_price,
    mp.unit_price - COALESCE(CAST(mp.previous_unit_price AS DECIMAL), 0) as descuento,
    ROUND(
        ((COALESCE(CAST(mp.previous_unit_price AS DECIMAL), mp.unit_price) - mp.unit_price) / 
         COALESCE(CAST(mp.previous_unit_price AS DECIMAL), mp.unit_price)) * 100, 
        2
    ) as porcentaje_descuento,
    mp.categoria_name,
    mp.subcategoria_name,
    mp.share_url,
    mp.thumbnail,
    mp.extraction_date
FROM mercadona_productos mp
WHERE mp.price_decreased = true 
AND mp.published = true
ORDER BY porcentaje_descuento DESC;

-- Vista: resumen_productos
-- Descripción: Resumen agregado de productos más comprados
CREATE VIEW resumen_productos AS
SELECT 
    p.descripcion,
    COUNT(*) as veces_comprado,
    SUM(p.cantidad) as cantidad_total,
    ROUND(AVG(p.precio_total), 2) as precio_promedio,
    ROUND(SUM(p.precio_total), 2) as gasto_total,
    MIN(t.fecha_compra) as primera_compra,
    MAX(t.fecha_compra) as ultima_compra
FROM productos p
JOIN tickets t ON p.ticket_id = t.id
GROUP BY p.descripcion
ORDER BY gasto_total DESC;

-- Vista: estadisticas_procesamiento
-- Descripción: Estadísticas de procesamiento por estado
CREATE VIEW estadisticas_procesamiento AS
SELECT 
    status,
    COUNT(*) as total,
    AVG(attempts) as promedio_intentos,
    MIN(created_at) as primer_intento,
    MAX(last_attempt) as ultimo_intento
FROM processing_log
GROUP BY status
ORDER BY total DESC;

-- Vista: usuarios_activos
-- Descripción: Usuarios activos con opt-in confirmado para reportes
CREATE VIEW usuarios_activos AS
SELECT 
    id,
    email,
    fecha_opt_in,
    preferencias_reporte,
    ultimo_reporte_enviado,
    created_at
FROM usuarios
WHERE activo = true 
AND opt_in_confirmado = true;

-- =============================================================================
-- FUNCIONES ÚTILES
-- =============================================================================

-- Función: gastos_por_categoria_periodo
-- Descripción: Calcula gastos por categoría en un período
CREATE OR REPLACE FUNCTION gastos_por_categoria_periodo(
    fecha_inicio DATE,
    fecha_fin DATE
) RETURNS TABLE(
    categoria_id INTEGER,
    categoria_nombre VARCHAR(100),
    num_productos BIGINT,
    gasto_total NUMERIC,
    precio_promedio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.nombre,
        COUNT(p.id)::BIGINT,
        ROUND(SUM(p.precio_total), 2),
        ROUND(AVG(p.precio_total), 2)
    FROM categorias c
    JOIN productos p ON c.id = p.categoria_id
    JOIN tickets t ON p.ticket_id = t.id
    WHERE t.fecha_compra BETWEEN fecha_inicio AND fecha_fin
    GROUP BY c.id, c.nombre
    ORDER BY SUM(p.precio_total) DESC;
END;
$$ LANGUAGE plpgsql;

-- Función: productos_mas_comprados_categoria
-- Descripción: Productos más comprados de una categoría
CREATE OR REPLACE FUNCTION productos_mas_comprados_categoria(
    cat_id INTEGER,
    limite INTEGER DEFAULT 10
) RETURNS TABLE(
    descripcion VARCHAR(200),
    veces_comprado BIGINT,
    cantidad_total BIGINT,
    gasto_total NUMERIC,
    precio_promedio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.descripcion,
        COUNT(*)::BIGINT,
        SUM(p.cantidad)::BIGINT,
        ROUND(SUM(p.precio_total), 2),
        ROUND(AVG(p.precio_total), 2)
    FROM productos p
    WHERE p.categoria_id = cat_id
    GROUP BY p.descripcion
    ORDER BY SUM(p.precio_total) DESC
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Función: obtener_gastos_periodo
-- Descripción: Calcula el total gastado en un período
CREATE OR REPLACE FUNCTION obtener_gastos_periodo(
    fecha_inicio DATE,
    fecha_fin DATE
) RETURNS DECIMAL AS $$
BEGIN
    RETURN COALESCE(
        (SELECT SUM(total) 
         FROM tickets 
         WHERE fecha_compra BETWEEN fecha_inicio AND fecha_fin),
        0
    );
END;
$$ LANGUAGE plpgsql;

-- Función: limpiar_logs_antiguos
-- Descripción: Limpia logs de procesamiento antiguos (más de 6 meses)
CREATE OR REPLACE FUNCTION limpiar_logs_antiguos() RETURNS INTEGER AS $$
DECLARE
    registros_eliminados INTEGER;
BEGIN
    DELETE FROM processing_log 
    WHERE created_at < CURRENT_DATE - INTERVAL '6 months'
    AND status IN ('completed', 'failed');
    
    GET DIAGNOSTICS registros_eliminados = ROW_COUNT;
    RETURN registros_eliminados;
END;
$$ LANGUAGE plpgsql;

-- Función: confirmar_opt_in_usuario
-- Descripción: Confirma el opt-in de un usuario usando su token
c
-- Función: obtener_usuarios_para_reporte
-- Descripción: Obtiene usuarios activos que deben recibir un tipo de reporte
CREATE OR REPLACE FUNCTION obtener_usuarios_para_reporte(
    tipo_reporte VARCHAR(20)
) RETURNS TABLE(email VARCHAR(255)) AS $$
BEGIN
    RETURN QUERY
    SELECT u.email
    FROM usuarios u
    WHERE u.activo = true 
    AND u.opt_in_confirmado = true
    AND (u.preferencias_reporte->tipo_reporte)::boolean = true;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DATOS INICIALES (OPCIONAL)
-- =============================================================================

-- Insertar tienda principal de Mercadona (ejemplo)
INSERT INTO tiendas (nombre, cif, direccion, codigo_postal, ciudad, telefono) 
VALUES (
    'MERCADONA, S.A.', 
    'A-46103834', 
    'Calle Ejemplo, 123', 
    '28000', 
    'Madrid', 
    '912345678'
) ON CONFLICT (cif) DO NOTHING;

-- Insertar usuario administrador ejemplo
INSERT INTO usuarios (email, activo, opt_in_confirmado, fecha_opt_in)
VALUES (
    'admin@ejemplo.com',
    true,
    true,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- PERMISOS Y SEGURIDAD
-- =============================================================================

-- Crear usuario para la aplicación (opcional)
-- CREATE USER mercadona_app WITH PASSWORD 'password_seguro';

-- Otorgar permisos necesarios
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mercadona_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mercadona_app;

-- =============================================================================
-- COMENTARIOS EN TABLAS Y COLUMNAS
-- =============================================================================

-- Comentarios en tablas
COMMENT ON TABLE usuarios IS 'Usuarios del sistema para envío de reportes';
COMMENT ON TABLE tiendas IS 'Información de las tiendas de Mercadona';
COMMENT ON TABLE tickets IS 'Tickets de compra procesados';
COMMENT ON TABLE productos IS 'Productos individuales de cada ticket';
COMMENT ON TABLE processing_log IS 'Log de procesamiento para debugging';
COMMENT ON TABLE file_backups IS 'Backup de archivos procesados';
COMMENT ON TABLE categorias IS 'Categorías principales de productos de Mercadona';
COMMENT ON TABLE subcategorias IS 'Subcategorías de productos de Mercadona';
COMMENT ON TABLE mercadona_productos IS 'Productos extraídos de la API de Mercadona';

-- Comentarios en columnas clave
COMMENT ON COLUMN usuarios.email IS 'Email del usuario para recibir reportes';
COMMENT ON COLUMN usuarios.activo IS 'Si el usuario está activo en el sistema';
COMMENT ON COLUMN usuarios.opt_in_confirmado IS 'Si el usuario ha confirmado recibir reportes';
COMMENT ON COLUMN usuarios.fecha_opt_in IS 'Fecha de confirmación del opt-in';
COMMENT ON COLUMN usuarios.token_confirmacion IS 'Token para confirmación de opt-in';
COMMENT ON COLUMN usuarios.preferencias_reporte IS 'Preferencias JSON de tipos de reporte';
COMMENT ON COLUMN tickets.numero_factura IS 'Número único de factura del ticket';
COMMENT ON COLUMN processing_log.status IS 'Estado actual del procesamiento';
COMMENT ON COLUMN processing_log.attempts IS 'Número de intentos de procesamiento';
COMMENT ON COLUMN file_backups.file_type IS 'Tipo de archivo: pdf, text, image';
COMMENT ON COLUMN productos.mercadona_producto_id IS 'ID del producto en el catálogo de Mercadona';
COMMENT ON COLUMN productos.categoria_id IS 'ID de la categoría detectada';
COMMENT ON COLUMN productos.subcategoria_id IS 'ID de la subcategoría detectada';
COMMENT ON COLUMN productos.categoria_detectada IS 'Nombre de la categoría detectada';
COMMENT ON COLUMN productos.subcategoria_detectada IS 'Nombre de la subcategoría detectada';
COMMENT ON COLUMN productos.confidence_score IS 'Puntuación de confianza del matching (0-1)';
COMMENT ON COLUMN productos.matching_method IS 'Método usado para el matching (exact, fuzzy, keywords, price)';
COMMENT ON COLUMN categorias.nombre IS 'Nombre de la categoría principal';
COMMENT ON COLUMN categorias.orden IS 'Orden de visualización de la categoría';
COMMENT ON COLUMN subcategorias.categoria_id IS 'ID de la categoría padre';
COMMENT ON COLUMN subcategorias.nombre IS 'Nombre de la subcategoría';
COMMENT ON COLUMN subcategorias.layout IS 'Tipo de layout para visualización';
COMMENT ON COLUMN subcategorias.published IS 'Si la subcategoría está publicada';

-- =============================================================================
-- FIN DEL DDL
-- =============================================================================

-- Para verificar la creación exitosa:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;