#!/usr/bin/env python3
"""
Script de inicialización de base de datos para Render.

Este script configura la base de datos en Render PostgreSQL:
1. Crea las tablas necesarias
2. Carga datos iniciales (categorías)
3. Verifica la conexión
"""

import sys
import os
from pathlib import Path

# Añadir src al path para importar mercagasto
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mercagasto.config.settings import get_database_config
from mercagasto.storage.postgresql import PostgreSQLTicketStorage
from mercagasto.config.logging import setup_logger

logger = setup_logger(__name__)


def run_sql_file(storage: PostgreSQLTicketStorage, sql_file: Path) -> bool:
    """Ejecuta un archivo SQL."""
    try:
        with sql_file.open('r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                # Ejecutar SQL por bloques separados por ';'
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        logger.info(f"Ejecutando: {statement[:50]}...")
                        cursor.execute(statement)
                        
        logger.info(f"✅ Archivo SQL ejecutado: {sql_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando {sql_file.name}: {e}")
        return False


def load_categories_data(storage: PostgreSQLTicketStorage) -> bool:
    """Carga datos de categorías desde JSON."""
    try:
        import json
        
        categories_file = Path(__file__).parent / "src" / "mercagasto" / "storage" / "data" / "categorias.json"
        
        if not categories_file.exists():
            logger.warning(f"Archivo de categorías no encontrado: {categories_file}")
            return True  # No es crítico
            
        with categories_file.open('r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                # Insertar categorías
                for cat in categories_data:
                    cursor.execute("""
                        INSERT INTO categorias (nombre, descripcion, color) 
                        VALUES (%s, %s, %s) 
                        ON CONFLICT (nombre) DO NOTHING
                    """, (cat['nombre'], cat.get('descripcion', ''), cat.get('color', '#808080')))
                    
                    # Insertar subcategorías
                    for subcat in cat.get('subcategorias', []):
                        cursor.execute("""
                            INSERT INTO subcategorias (categoria_id, nombre, descripcion) 
                            SELECT id, %s, %s FROM categorias WHERE nombre = %s
                            ON CONFLICT (categoria_id, nombre) DO NOTHING
                        """, (subcat['nombre'], subcat.get('descripcion', ''), cat['nombre']))
        
        logger.info("✅ Datos de categorías cargados")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cargando categorías: {e}")
        return False


def verify_setup(storage: PostgreSQLTicketStorage) -> bool:
    """Verifica que la configuración esté correcta."""
    try:
        with storage.get_connection() as conn:
            with conn.cursor() as cursor:
                # Verificar tablas principales
                tables_to_check = [
                    'tickets', 'productos', 'categorias', 'subcategorias', 
                    'mercadona_productos', 'productos_categorized_view'
                ]
                
                for table in tables_to_check:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table,))
                    
                    exists = cursor.fetchone()[0]
                    if exists:
                        logger.info(f"✅ Tabla {table} existe")
                    else:
                        logger.warning(f"⚠️  Tabla {table} no encontrada")
                
                # Contar registros en tablas clave
                cursor.execute("SELECT COUNT(*) FROM categorias")
                cat_count = cursor.fetchone()[0]
                logger.info(f"📊 Categorías: {cat_count}")
                
                cursor.execute("SELECT COUNT(*) FROM subcategorias")
                subcat_count = cursor.fetchone()[0]
                logger.info(f"📊 Subcategorías: {subcat_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {e}")
        return False


def main():
    """Función principal de inicialización."""
    logger.info("🚀 Iniciando configuración de base de datos para Render")
    
    try:
        # Obtener configuración
        config = get_database_config()
        logger.info(f"📊 Conectando a: {config.host}:{config.port}/{config.database}")
        
        # Crear storage
        storage = PostgreSQLTicketStorage(config)
        
        # Verificar conexión
        with storage.get_connection() as conn:
            logger.info("✅ Conexión a base de datos exitosa")
        
        # Ejecutar schema.sql
        schema_file = Path(__file__).parent / "src" / "mercagasto" / "storage" / "schema.sql"
        if schema_file.exists():
            if not run_sql_file(storage, schema_file):
                logger.error("❌ Error ejecutando schema.sql")
                return False
        else:
            logger.warning("⚠️  Archivo schema.sql no encontrado")
        
        # Cargar datos de categorías
        if not load_categories_data(storage):
            logger.warning("⚠️  No se pudieron cargar las categorías")
        
        # Verificar setup
        if not verify_setup(storage):
            logger.error("❌ Error en verificación final")
            return False
        
        logger.info("🎉 ¡Configuración de base de datos completada exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fatal en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)