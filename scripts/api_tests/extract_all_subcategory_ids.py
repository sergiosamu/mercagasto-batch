#!/usr/bin/env python3
"""
Script para extraer todos los IDs de subcategorías del archivo categorias.json
"""
import json

def extract_all_subcategory_ids():
    """Extrae todos los IDs de subcategorías del JSON."""
    
    # Cargar categorías
    with open('src/mercagasto/storage/data/categorias.json', 'r') as f:
        data = json.load(f)
    
    # Extraer todos los IDs de subcategorías
    subcategory_ids = []
    for main_category in data['results']:
        for subcategory in main_category['categories']:
            subcategory_ids.append(subcategory['id'])
    
    # Convertir a string separado por comas para usar directamente
    ids_string = ','.join(map(str, subcategory_ids))
    
    print(f"Total subcategorías encontradas: {len(subcategory_ids)}")
    print(f"IDs de subcategorías: {ids_string}")
    
    return subcategory_ids, ids_string

if __name__ == "__main__":
    subcategory_ids, ids_string = extract_all_subcategory_ids()
    
    # Guardar en archivo para referencia
    with open('all_subcategory_ids.txt', 'w') as f:
        f.write(ids_string)
    
    print(f"\nIDs guardados en: all_subcategory_ids.txt")
    print(f"\nPara cargar todos los productos ejecuta:")
    print(f'uv run python extract_and_load_products.py --categories "{ids_string}"')