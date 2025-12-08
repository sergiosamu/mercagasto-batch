"""
Ejecutor simple para test de integración de tickets.
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tests.test_ticket_database_integration import TestTicketIntegration

def run_simple_integration_test():
    """Ejecuta el test de integración de forma simple."""
    
    print("🧪 Iniciando test de integración...")
    
    # Crear instancia de test
    test_instance = TestTicketIntegration()
    
    try:
        # Setup de clase
        TestTicketIntegration.setup_class()
        
        print("\n1️⃣  Test de conexión a BD...")
        test_instance.test_database_connection()
        print("   ✅ Conexión exitosa")
        
        print("\n2️⃣  Test de procesamiento completo con ticket simulado...")
        test_instance.test_complete_ticket_processing_simulation()
        print("   ✅ Procesamiento completo exitoso")
        
        print("\n3️⃣  Test de manejo de duplicados...")
        test_instance.test_duplicate_ticket_handling()
        print("   ✅ Manejo de duplicados exitoso")
        
        print("\n4️⃣  Test de tickets inválidos...")
        test_instance.test_invalid_ticket_handling()
        print("   ✅ Manejo de tickets inválidos exitoso")
        
        print("\n🎉 ¡Todos los tests de integración pasaron!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en test de integración: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpieza
        try:
            TestTicketIntegration.teardown_class()
        except Exception as e:
            print(f"⚠️  Error en limpieza: {e}")

if __name__ == "__main__":
    success = run_simple_integration_test()
    exit(0 if success else 1)