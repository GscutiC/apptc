"""
Entidad Convocation para gestión de convocatorias Techo Propio
Representa un período de postulación con código único
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass
from .base_entity import TechoPropioBaseEntity


@dataclass 
class Convocation(TechoPropioBaseEntity):
    """
    Entidad que representa una convocatoria del programa Techo Propio
    Define períodos de postulación con códigos únicos
    """
    
    # Campos obligatorios (sin valores por defecto)
    code: str  # Código único: CONV-2025-01, CONV-2025-02, etc.
    title: str  # Título descriptivo: "Primera Convocatoria 2025"
    start_date: date  # Fecha de inicio de la convocatoria
    end_date: date   # Fecha de cierre de la convocatoria
    
    # Campos opcionales (con valores por defecto)
    description: Optional[str] = None  # Descripción detallada
    is_active: bool = True  # Si está activa para recibir solicitudes
    is_published: bool = False  # Si está publicada y visible
    max_applications: Optional[int] = None  # Límite de solicitudes (opcional)
    year: Optional[int] = None  # Año de la convocatoria (derivado)
    sequential_number: Optional[int] = None  # Número secuencial en el año
    
    def __post_init__(self):
        """Validaciones y cálculos automáticos"""
        super().__init__()
        
        # Derivar año si no está establecido
        if not self.year:
            self.year = self.start_date.year if self.start_date else datetime.now().year
        
        # Validar fechas
        self._validate_dates()
        
        # Validar código único
        self._validate_code_format()
    
    def _validate_dates(self) -> None:
        """Validar consistencia de fechas"""
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        
        # Validar que no sea muy antigua
        if self.start_date and self.start_date.year < 2020:
            raise ValueError("La fecha de inicio no puede ser anterior a 2020")
    
    def _validate_code_format(self) -> None:
        """Validar formato del código de convocatoria"""
        if not self.code:
            raise ValueError("El código de convocatoria es obligatorio")
        
        # Formato esperado: CONV-YYYY-XX
        if not self.code.startswith("CONV-"):
            raise ValueError("El código debe comenzar con 'CONV-'")
        
        parts = self.code.split("-")
        if len(parts) != 3:
            raise ValueError("Formato de código inválido. Use: CONV-YYYY-XX")
        
        try:
            year = int(parts[1])
            seq = int(parts[2])
            if year < 2020 or year > 2030:
                raise ValueError("Año en el código debe estar entre 2020 y 2030")
            if seq < 1 or seq > 99:
                raise ValueError("Número secuencial debe estar entre 01 y 99")
        except ValueError:
            raise ValueError("Formato de código inválido. Use: CONV-YYYY-XX")
    
    @property
    def is_current(self) -> bool:
        """Verificar si la convocatoria está en período vigente"""
        today = date.today()
        return (
            self.is_active and 
            self.start_date <= today <= self.end_date
        )
    
    @property
    def is_upcoming(self) -> bool:
        """Verificar si la convocatoria es futura"""
        today = date.today()
        return self.start_date > today
    
    @property
    def is_expired(self) -> bool:
        """Verificar si la convocatoria ha expirado"""
        today = date.today()
        return self.end_date < today
    
    @property
    def status_display(self) -> str:
        """Estado de la convocatoria en texto legible"""
        if not self.is_active:
            return "Inactiva"
        elif self.is_upcoming:
            return "Próxima"
        elif self.is_current:
            return "Vigente"
        elif self.is_expired:
            return "Expirada"
        else:
            return "Pendiente"
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Días restantes de la convocatoria"""
        if self.is_current:
            return (self.end_date - date.today()).days
        return None
    
    def activate(self) -> None:
        """Activar la convocatoria"""
        self.is_active = True
        self.update_timestamp()
    
    def deactivate(self) -> None:
        """Desactivar la convocatoria"""
        self.is_active = False
        self.update_timestamp()
    
    def publish(self) -> None:
        """Publicar la convocatoria (hacerla visible)"""
        self.is_published = True
        self.update_timestamp()
    
    def unpublish(self) -> None:
        """Despublicar la convocatoria"""
        self.is_published = False
        self.update_timestamp()
    
    def extend_deadline(self, new_end_date: date) -> None:
        """Extender fecha límite de la convocatoria"""
        if new_end_date <= self.end_date:
            raise ValueError("La nueva fecha debe ser posterior a la actual")
        
        self.end_date = new_end_date
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para API responses"""
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "is_published": self.is_published,
            "max_applications": self.max_applications,
            "year": self.year,
            "sequential_number": self.sequential_number,
            "status_display": self.status_display,
            "is_current": self.is_current,
            "is_upcoming": self.is_upcoming,
            "is_expired": self.is_expired,
            "days_remaining": self.days_remaining,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @staticmethod
    def generate_code(year: int, sequential: int) -> str:
        """Generar código de convocatoria estandarizado"""
        return f"CONV-{year}-{sequential:02d}"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Convocation':
        """Crear instancia desde diccionario"""
        return cls(
            entity_id=data.get("id"),
            code=data["code"],
            title=data["title"],
            description=data.get("description"),
            start_date=datetime.fromisoformat(data["start_date"]).date() if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]).date() if data.get("end_date") else None,
            is_active=data.get("is_active", True),
            is_published=data.get("is_published", False),
            max_applications=data.get("max_applications"),
            year=data.get("year"),
            sequential_number=data.get("sequential_number"),
            created_by=data.get("created_by")
        )