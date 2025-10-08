"""
Script rápido para diagnosticar el endpoint seguro
"""
import requests

def test_interface_config_endpoints():
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/api/interface-config/current",
        "/api/interface-config/current/safe"
    ]
    
    print("🔍 Probando endpoints de configuración de interfaz...")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url)
            print(f"\n📡 GET {endpoint}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 401:
                print("   ✅ Correctamente requiere autenticación")
            elif response.status_code == 403:
                print("   ❌ Forbidden - problema de permisos")
            elif response.status_code == 404:
                print("   ❌ Not Found - endpoint no existe")  
            elif response.status_code == 200:
                print("   ✅ OK - endpoint funciona")
            else:
                print(f"   ⚠️ Código inesperado: {response.status_code}")
                
            if hasattr(response, 'json'):
                try:
                    data = response.json()
                    if 'detail' in data:
                        print(f"   Detalle: {data['detail']}")
                except:
                    pass
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_interface_config_endpoints()