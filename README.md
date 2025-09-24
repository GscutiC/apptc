# mi_app_completa_backend

Proyecto con arquitectura hexagonal usando python y mongodb.

## Estructura del Proyecto

```
src/mi_app_completa_backend/
├── domain/              # Lógica de negocio
│   ├── entities/        # Entidades del dominio
│   ├── repositories/    # Interfaces de repositorios
│   ├── services/        # Servicios del dominio
│   └── value_objects/   # Objetos de valor
├── application/         # Casos de uso
│   ├── use_cases/       # Casos de uso específicos
│   └── dto/            # Data Transfer Objects
└── infrastructure/     # Adaptadores externos
    ├── persistence/     # Implementación de repositorios
    ├── web/            # API REST
    └── config/         # Configuración
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python -m src.mi_app_completa_backend.infrastructure.web.fastapi.main
```

## Tests

```bash
pytest
```