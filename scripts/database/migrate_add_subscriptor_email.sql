-- =============================================================================
-- MIGRACIÓN: Agregar subscriptor_id a tablas existentes
-- =============================================================================

-- 1. Crear tabla subscribed_emails si no existe (debe crearse antes de las FK)
CREATE TABLE IF NOT EXISTS subscribed_emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Insertar email del usuario actual (ajustar según sea necesario)
INSERT INTO subscribed_emails (email) 
VALUES ('sergio.sanchez.munoz@gmail.com')
ON CONFLICT (email) DO NOTHING;

-- 3. Agregar columna subscriptor_id a la tabla tickets (nullable inicialmente)
ALTER TABLE tickets 
ADD COLUMN IF NOT EXISTS subscriptor_id INTEGER REFERENCES subscribed_emails(id);

-- 4. Agregar columna subscriptor_id a la tabla processing_log (nullable inicialmente)
ALTER TABLE processing_log 
ADD COLUMN IF NOT EXISTS subscriptor_id INTEGER REFERENCES subscribed_emails(id);

-- 5. Crear índices para las nuevas columnas
CREATE INDEX IF NOT EXISTS idx_tickets_subscriptor ON tickets(subscriptor_id);
CREATE INDEX IF NOT EXISTS idx_processing_subscriptor ON processing_log(subscriptor_id);

-- 6. Función auxiliar para obtener ID de subscriptor por email
CREATE OR REPLACE FUNCTION get_subscriptor_id(user_email VARCHAR(255)) 
RETURNS INTEGER AS $$
DECLARE
    subscriptor_id INTEGER;
BEGIN
    SELECT id INTO subscriptor_id 
    FROM subscribed_emails 
    WHERE LOWER(email) = LOWER(user_email);
    
    IF subscriptor_id IS NULL THEN
        -- Si no existe, lo insertamos
        INSERT INTO subscribed_emails (email) 
        VALUES (user_email) 
        ON CONFLICT (email) DO NOTHING
        RETURNING id INTO subscriptor_id;
        
        -- Si el INSERT no devolvió nada (por conflicto), obtenemos el ID
        IF subscriptor_id IS NULL THEN
            SELECT id INTO subscriptor_id 
            FROM subscribed_emails 
            WHERE LOWER(email) = LOWER(user_email);
        END IF;
    END IF;
    
    RETURN subscriptor_id;
END;
$$ LANGUAGE plpgsql;

-- 7. Comentarios para documentar los cambios
COMMENT ON COLUMN tickets.subscriptor_id IS 'ID del subscriptor que envió este ticket';
COMMENT ON COLUMN processing_log.subscriptor_id IS 'ID del subscriptor del mensaje procesado';
COMMENT ON FUNCTION get_subscriptor_id(VARCHAR) IS 'Obtiene o crea un subscriptor y retorna su ID';

-- 8. Verificar la migración
SELECT 
    'tickets' as tabla,
    COUNT(*) as total_registros,
    COUNT(subscriptor_id) as con_subscriptor_id
FROM tickets

UNION ALL

SELECT 
    'processing_log' as tabla,
    COUNT(*) as total_registros,
    COUNT(subscriptor_id) as con_subscriptor_id
FROM processing_log

UNION ALL

SELECT 
    'subscribed_emails' as tabla,
    COUNT(*) as total_registros,
    COUNT(email) as emails_activos
FROM subscribed_emails;
