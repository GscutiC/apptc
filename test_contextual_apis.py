"""
Script para probar las APIs contextuales
Valida que los endpoints estén funcionando correctamente
"""

import requests
import json
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/contextual-config"

# Token JWT - obtén uno válido ejecutando el código JavaScript en la consola
# 1. Ve a http://localhost:3000 y haz login
# 2. F12 → Console → ejecuta: window.Clerk.session.getToken().then(t => console.log(t))
JWT_TOKEN = None  # Pegar token aquí cuando lo obtengas

def make_request(method: str, endpoint: str, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> Dict[Any, Any]:
    """Hace una request HTTP y retorna la respuesta"""
    url = f"{API_URL}{endpoint}"
    
    default_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if JWT_TOKEN:
        default_headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Método HTTP no soportado: {method}")
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response.json() if response.content else None,
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "error": str(e),
            "success": False
        }
    except json.JSONDecodeError:
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text,
            "success": 200 <= response.status_code < 300
        }

def test_endpoints_availability():
    """Prueba que los endpoints estén disponibles"""
    print("🔍 Probando disponibilidad de endpoints contextuales...")
    
    # Endpoints a probar
    endpoints = [
        ("GET", "/health"),  # Si existe
        ("GET", "/effective/test-user-id"),
        ("GET", "/user/test-user-id"),
        ("GET", "/permissions/global"),
        ("POST", "/preferences"),
    ]
    
    results = {}
    
    for method, endpoint in endpoints:
        print(f"\n📡 {method} {API_URL}{endpoint}")
        
        # Datos de prueba para POST
        test_data = None
        if method == "POST" and endpoint == "/preferences":
            test_data = {
                "user_id": "test-user",
                "preferences": {
                    "theme": {"primary": {"500": "#000000"}},
                    "branding": {"title": "Test"}
                }
            }
        
        result = make_request(method, endpoint, test_data)
        results[f"{method} {endpoint}"] = result
        
        if result["success"]:
            print(f"  ✅ {result['status_code']} - OK")
        else:
            print(f"  ❌ {result['status_code']} - {result.get('error', 'Error')}")
            if 'data' in result:
                print(f"     Detalle: {result['data']}")
    
    return results

def test_with_auth_token():
    """Prueba con token de autenticación"""
    print("\n🔐 Para pruebas con autenticación:")
    print("1. Ve a tu aplicación en el navegador")
    print("2. Abre DevTools (F12)")
    print("3. En la consola, ejecuta: localStorage.getItem('__clerk_db_jwt')")
    print("4. Copia el token y pégalo en JWT_TOKEN en este script")
    print("5. Ejecuta de nuevo este script")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de APIs contextuales...")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📍 API URL: {API_URL}")
    
    if not JWT_TOKEN:
        print("\n⚠️  Sin token JWT - probando sin autenticación")
    else:
        print(f"\n🔑 Token JWT configurado: {JWT_TOKEN[:20]}...")
    
    # Probar disponibilidad
    results = test_endpoints_availability()
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS:")
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"✅ Exitosas: {successful}/{total}")
    print(f"❌ Fallidas: {total - successful}/{total}")
    
    if not JWT_TOKEN:
        test_with_auth_token()
    
    # Mostrar detalles de errores
    print("\n🔍 DETALLES DE ERRORES:")
    for endpoint, result in results.items():
        if not result["success"]:
            print(f"\n❌ {endpoint}")
            print(f"   Status: {result['status_code']}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            if 'data' in result:
                print(f"   Data: {result['data']}")
            if 'text' in result:
                print(f"   Text: {result['text']}")

if __name__ == "__main__":
    main()