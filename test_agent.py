"""
Test rápido para verificar que el agente dinámico está bien integrado.
Ejecutar: python test_agent.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/agent"

def test_agent_chat():
    """Test el endpoint del agente"""
    
    test_cases = [
        {
            "name": "Crear categoría",
            "message": "Crea una categoría llamada 'marca' con los atributos samsung y lg",
            "expected_action": "crear_categoria"
        },
        {
            "name": "Listar categorías",
            "message": "Muestra todas las categorías",
            "expected_action": "listar_categorias"
        },
        {
            "name": "Agregar atributo",
            "message": "Agregá 'sony' a la categoría marca",
            "expected_action": "agregar_atributo"
        },
        {
            "name": "Aumentar precios",
            "message": "Aumenta 20% los precios de samsung",
            "expected_action": "aumentar_precios"
        },
        {
            "name": "Consulta general",
            "message": "¿Cuál es un buen margen de ganancia?",
            "expected_action": None  # No ejecuta acción
        },
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"Mensaje: {test['message']}")
        print(f"{'='*60}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "message": test["message"],
                    "conversation_history": []
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ Respuesta exitosa")
            print(f"Message: {data.get('message')[:100]}...")
            print(f"Action: {data.get('action_executed')}")
            print(f"Success: {data.get('success')}")
            
            if data.get('action_executed') != test.get('expected_action'):
                print(f"⚠️  AVISO: Se esperaba '{test['expected_action']}' pero obtuvo '{data.get('action_executed')}'")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR: No se pude conectar al servidor en {BASE_URL}")
            print("Asegúrate de que el backend esté corriendo")
            break
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")


if __name__ == "__main__":
    print("🤖 Testing Agente Dinámico de IA")
    print("Asegúrate de que el backend está corriendo en http://localhost:8000")
    input("Presiona Enter para comenzar...")
    test_agent_chat()
    print("\n✅ Tests completados")
