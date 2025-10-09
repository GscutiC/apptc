# 🌐 Guía de Integración Frontend - APIs Gubernamentales

Guía completa para integrar las APIs gubernamentales en tu aplicación React/Next.js.

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Servicio API en TypeScript](#servicio-api-en-typescript)
3. [Hooks de React](#hooks-de-react)
4. [Componentes de Ejemplo](#componentes-de-ejemplo)
5. [Manejo de Errores](#manejo-de-errores)
6. [Best Practices](#best-practices)

---

## 🔧 Configuración Inicial

### 1. Variables de Entorno

Crear archivo `.env.local`:

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
# o en producción:
# NEXT_PUBLIC_API_URL=https://api.tuapp.com
```

### 2. Tipos TypeScript

Crear `types/government.ts`:

```typescript
// types/government.ts

export interface DniData {
  dni: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno: string;
  apellidos: string;
  nombre_completo: string;
  fecha_nacimiento?: string;
  estado_civil?: string;
  ubigeo?: string;
  direccion?: string;
  restricciones?: string;
}

export interface RucData {
  ruc: string;
  razon_social: string;
  nombre_comercial?: string;
  estado: string;
  condicion?: string;
  tipo_empresa?: string;
  direccion?: string;
  departamento?: string;
  provincia?: string;
  distrito?: string;
  fecha_inscripcion?: string;
  actividad_economica?: string;
  telefono?: string;
  email?: string;
  representante_legal?: string;
  trabajadores?: number;
}

export interface DniResponse {
  success: boolean;
  message: string;
  data: DniData | null;
  fuente?: string;
  timestamp: string;
  cache_hit: boolean;
}

export interface RucResponse {
  success: boolean;
  message: string;
  data: RucData | null;
  fuente?: string;
  timestamp: string;
  cache_hit: boolean;
}

export interface ApiError {
  detail: string;
  status?: number;
}
```

---

## 🛠️ Servicio API en TypeScript

### Servicio Completo

Crear `services/governmentApi.ts`:

```typescript
// services/governmentApi.ts

import { DniResponse, RucResponse, ApiError } from '@/types/government';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class GovernmentApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(token?: string) {
    this.baseUrl = `${API_URL}/api/government`;
    this.token = token || null;
  }

  /**
   * Configurar token de autenticación
   */
  setToken(token: string) {
    this.token = token;
  }

  /**
   * Headers base para todas las peticiones
   */
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  /**
   * Consultar DNI en RENIEC
   */
  async queryDni(dni: string, useCache: boolean = true): Promise<DniResponse> {
    try {
      const response = await fetch(
        `${this.baseUrl}/dni/${dni}?use_cache=${useCache}`,
        {
          method: 'GET',
          headers: this.getHeaders(),
        }
      );

      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.detail || 'Error consultando DNI');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en queryDni:', error);
      throw error;
    }
  }

  /**
   * Consultar RUC en SUNAT
   */
  async queryRuc(ruc: string, useCache: boolean = true): Promise<RucResponse> {
    try {
      const response = await fetch(
        `${this.baseUrl}/ruc/${ruc}?use_cache=${useCache}`,
        {
          method: 'GET',
          headers: this.getHeaders(),
        }
      );

      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.detail || 'Error consultando RUC');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en queryRuc:', error);
      throw error;
    }
  }

  /**
   * Obtener proveedores disponibles
   */
  async getProviders() {
    try {
      const response = await fetch(`${this.baseUrl}/providers`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error('Error obteniendo proveedores');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en getProviders:', error);
      throw error;
    }
  }

  /**
   * Health check de servicios
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error('Error en health check');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en healthCheck:', error);
      throw error;
    }
  }

  /**
   * Validar formato de DNI (sin consultar API)
   */
  static validateDni(dni: string): boolean {
    return /^\d{8}$/.test(dni);
  }

  /**
   * Validar formato de RUC (sin consultar API)
   */
  static validateRuc(ruc: string): boolean {
    if (!/^\d{11}$/.test(ruc)) return false;
    const tipo = ruc.substring(0, 2);
    return ['10', '15', '17', '20'].includes(tipo);
  }
}

// Instancia singleton
let apiInstance: GovernmentApiService | null = null;

export function getGovernmentApi(token?: string): GovernmentApiService {
  if (!apiInstance || token) {
    apiInstance = new GovernmentApiService(token);
  }
  return apiInstance;
}
```

---

## 🪝 Hooks de React

### Hook para Consulta DNI

Crear `hooks/useQueryDni.ts`:

```typescript
// hooks/useQueryDni.ts

import { useState } from 'react';
import { DniData, DniResponse } from '@/types/government';
import { getGovernmentApi } from '@/services/governmentApi';
import { useAuth } from '@clerk/nextjs'; // O tu sistema de auth

export function useQueryDni() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DniData | null>(null);

  const queryDni = async (dni: string, useCache: boolean = true) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      // Obtener token de autenticación
      const token = await getToken();
      if (!token) {
        throw new Error('No autenticado');
      }

      // Crear instancia del servicio con token
      const api = getGovernmentApi(token);

      // Consultar DNI
      const response: DniResponse = await api.queryDni(dni, useCache);

      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError(response.message || 'No se encontró información');
      }

      return response;
    } catch (err: any) {
      const errorMessage = err.message || 'Error al consultar DNI';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
    setLoading(false);
  };

  return {
    queryDni,
    loading,
    error,
    data,
    reset,
  };
}
```

### Hook para Consulta RUC

Crear `hooks/useQueryRuc.ts`:

```typescript
// hooks/useQueryRuc.ts

import { useState } from 'react';
import { RucData, RucResponse } from '@/types/government';
import { getGovernmentApi } from '@/services/governmentApi';
import { useAuth } from '@clerk/nextjs';

export function useQueryRuc() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RucData | null>(null);

  const queryRuc = async (ruc: string, useCache: boolean = true) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error('No autenticado');
      }

      const api = getGovernmentApi(token);
      const response: RucResponse = await api.queryRuc(ruc, useCache);

      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError(response.message || 'No se encontró información');
      }

      return response;
    } catch (err: any) {
      const errorMessage = err.message || 'Error al consultar RUC';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
    setLoading(false);
  };

  return {
    queryRuc,
    loading,
    error,
    data,
    reset,
  };
}
```

---

## 🎨 Componentes de Ejemplo

### Componente para Búsqueda de DNI

```typescript
// components/DniSearch.tsx

'use client';

import { useState } from 'react';
import { useQueryDni } from '@/hooks/useQueryDni';
import { GovernmentApiService } from '@/services/governmentApi';

export default function DniSearch() {
  const [dni, setDni] = useState('');
  const [dniError, setDniError] = useState('');
  const { queryDni, loading, error, data, reset } = useQueryDni();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setDniError('');

    // Validar formato
    if (!GovernmentApiService.validateDni(dni)) {
      setDniError('DNI debe tener 8 dígitos numéricos');
      return;
    }

    try {
      await queryDni(dni);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Consultar DNI</h2>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={dni}
            onChange={(e) => {
              setDni(e.target.value);
              setDniError('');
            }}
            placeholder="Ingrese DNI (8 dígitos)"
            className="flex-1 px-4 py-2 border rounded-lg"
            maxLength={8}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Consultando...' : 'Buscar'}
          </button>
          {data && (
            <button
              type="button"
              onClick={reset}
              className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Limpiar
            </button>
          )}
        </div>
        {dniError && (
          <p className="text-red-500 text-sm mt-2">{dniError}</p>
        )}
      </form>

      {/* Loading state */}
      {loading && (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Consultando RENIEC...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-semibold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {/* Success state */}
      {data && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-800 mb-4">
            Información Encontrada
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">DNI</p>
              <p className="font-semibold">{data.dni}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Nombre Completo</p>
              <p className="font-semibold">{data.nombre_completo}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Nombres</p>
              <p className="font-semibold">{data.nombres}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Apellidos</p>
              <p className="font-semibold">{data.apellidos}</p>
            </div>
            {data.fecha_nacimiento && (
              <div>
                <p className="text-sm text-gray-600">Fecha de Nacimiento</p>
                <p className="font-semibold">{data.fecha_nacimiento}</p>
              </div>
            )}
            {data.estado_civil && (
              <div>
                <p className="text-sm text-gray-600">Estado Civil</p>
                <p className="font-semibold">{data.estado_civil}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

### Componente para Búsqueda de RUC

```typescript
// components/RucSearch.tsx

'use client';

import { useState } from 'react';
import { useQueryRuc } from '@/hooks/useQueryRuc';
import { GovernmentApiService } from '@/services/governmentApi';

export default function RucSearch() {
  const [ruc, setRuc] = useState('');
  const [rucError, setRucError] = useState('');
  const { queryRuc, loading, error, data, reset } = useQueryRuc();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRucError('');

    // Validar formato
    if (!GovernmentApiService.validateRuc(ruc)) {
      setRucError('RUC debe tener 11 dígitos y comenzar con 10, 15, 17 o 20');
      return;
    }

    try {
      await queryRuc(ruc);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Consultar RUC</h2>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={ruc}
            onChange={(e) => {
              setRuc(e.target.value);
              setRucError('');
            }}
            placeholder="Ingrese RUC (11 dígitos)"
            className="flex-1 px-4 py-2 border rounded-lg"
            maxLength={11}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Consultando...' : 'Buscar'}
          </button>
          {data && (
            <button
              type="button"
              onClick={reset}
              className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Limpiar
            </button>
          )}
        </div>
        {rucError && (
          <p className="text-red-500 text-sm mt-2">{rucError}</p>
        )}
      </form>

      {loading && (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Consultando SUNAT...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-semibold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {data && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-800 mb-4">
            Información de Empresa
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">RUC</p>
              <p className="font-semibold">{data.ruc}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Estado</p>
              <span className={`px-2 py-1 rounded text-sm font-semibold ${
                data.estado === 'ACTIVO' 
                  ? 'bg-green-200 text-green-800' 
                  : 'bg-red-200 text-red-800'
              }`}>
                {data.estado}
              </span>
            </div>
            <div className="col-span-2">
              <p className="text-sm text-gray-600">Razón Social</p>
              <p className="font-semibold text-lg">{data.razon_social}</p>
            </div>
            {data.direccion && (
              <div className="col-span-2">
                <p className="text-sm text-gray-600">Dirección</p>
                <p className="font-semibold">{data.direccion}</p>
              </div>
            )}
            {data.departamento && (
              <div>
                <p className="text-sm text-gray-600">Departamento</p>
                <p className="font-semibold">{data.departamento}</p>
              </div>
            )}
            {data.provincia && (
              <div>
                <p className="text-sm text-gray-600">Provincia</p>
                <p className="font-semibold">{data.provincia}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🚨 Manejo de Errores

```typescript
// utils/errorHandling.ts

export function handleApiError(error: any): string {
  if (error.response) {
    // Error de respuesta del servidor
    const status = error.response.status;
    const detail = error.response.data?.detail;

    switch (status) {
      case 400:
        return detail || 'Datos inválidos';
      case 401:
        return 'No autenticado. Por favor inicia sesión';
      case 403:
        return 'No tienes permisos para realizar esta acción';
      case 404:
        return detail || 'No se encontró información';
      case 503:
        return 'Servicio no disponible. Intenta nuevamente';
      default:
        return detail || 'Error en el servidor';
    }
  } else if (error.request) {
    // Sin respuesta del servidor
    return 'No se pudo conectar con el servidor';
  } else {
    // Error de configuración
    return error.message || 'Error desconocido';
  }
}
```

---

## ✨ Best Practices

### 1. **Usar Debounce para Búsquedas**

```typescript
import { useDebounce } from '@/hooks/useDebounce';

function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500);

  useEffect(() => {
    if (debouncedSearch && debouncedSearch.length === 8) {
      // Consultar automáticamente
      queryDni(debouncedSearch);
    }
  }, [debouncedSearch]);
}
```

### 2. **Cachear Resultados Localmente**

```typescript
const [cache, setCache] = useState<Map<string, DniData>>(new Map());

const queryWithCache = async (dni: string) => {
  // Verificar caché local
  if (cache.has(dni)) {
    setData(cache.get(dni)!);
    return;
  }

  // Consultar API
  const result = await queryDni(dni);
  if (result.success && result.data) {
    setCache(new Map(cache.set(dni, result.data)));
  }
};
```

### 3. **Validación en Tiempo Real**

```typescript
const validateInput = (value: string, type: 'dni' | 'ruc') => {
  if (type === 'dni') {
    if (value.length !== 8) return 'DNI debe tener 8 dígitos';
    if (!/^\d+$/.test(value)) return 'Solo números';
  }
  return '';
};
```

---

## 📝 Resumen

Ahora tienes:
- ✅ Servicio TypeScript completo
- ✅ Hooks de React reutilizables
- ✅ Componentes de ejemplo
- ✅ Manejo de errores robusto
- ✅ Best practices implementadas

**¡Tu frontend está listo para consumir las APIs gubernamentales!** 🚀
