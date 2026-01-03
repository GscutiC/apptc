"""
Entidad EconomicInfo para el módulo Techo Propio
Representa la información económica del solicitante y/o cónyuge
"""

from typing import Optional
from decimal import Decimal
from dataclasses import dataclass
from .base_entity import TechoPropioBaseEntity
from ...value_objects.techo_propio import (
    EmploymentSituation, WorkCondition, VALIDATION_CONSTANTS
)


@dataclass
class EconomicInfo(TechoPropioBaseEntity):
    """
    Entidad que representa información económica de un solicitante
    Incluye situación laboral, ingresos y condición de trabajo
    """
    
    # Campos obligatorios primero
    employment_situation: EmploymentSituation
    monthly_income: Decimal  # Ingreso mensual declarado
    applicant_id: str  # ID del solicitante al que pertenece esta información
    
    # Campos opcionales después
    work_condition: Optional[WorkCondition] = None  # Solo si está empleado
    occupation_detail: Optional[str] = None  # Detalle de la ocupación
    employer_name: Optional[str] = None  # Nombre del empleador (si es dependiente)
    has_additional_income: bool = False
    additional_income_amount: Optional[Decimal] = None
    additional_income_source: Optional[str] = None
    is_main_applicant: bool = True  # True para jefe familia, False para cónyuge
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        super().__init__()
        self._validate_income()
        self._validate_employment_consistency()
        self._validate_additional_income()
        self._clean_and_validate_strings()
    
    def _validate_income(self) -> None:
        """Validar ingresos"""
        min_income = VALIDATION_CONSTANTS["MIN_INCOME"]
        max_income = VALIDATION_CONSTANTS["MAX_INCOME"]
        
        if self.monthly_income < min_income:
            raise ValueError(f"El ingreso mensual no puede ser menor a {min_income}")
        if self.monthly_income > max_income:
            raise ValueError(f"El ingreso mensual no puede ser mayor a {max_income}")
    
    def _validate_employment_consistency(self) -> None:
        """Validar consistencia entre situación laboral y otros campos"""
        if self.employment_situation in [EmploymentSituation.DEPENDENT, EmploymentSituation.INDEPENDENT]:
            if not self.work_condition:
                raise ValueError("La condición de trabajo es obligatoria para empleados")
            if not self.occupation_detail:
                raise ValueError("El detalle de ocupación es obligatorio para empleados")
                
            # Para trabajadores dependientes, el empleador podría ser requerido
            if self.employment_situation == EmploymentSituation.DEPENDENT:
                if not self.employer_name or not self.employer_name.strip():
                    # No es error crítico, pero se recomienda
                    pass
        
        elif self.employment_situation in [EmploymentSituation.UNEMPLOYED, EmploymentSituation.RETIRED]:
            # Para desempleados o jubilados, no debería tener condición de trabajo
            if self.work_condition:
                self.work_condition = None  # Limpiar automáticamente
            if self.employer_name:
                self.employer_name = None  # Limpiar automáticamente
    
    def _validate_additional_income(self) -> None:
        """Validar información de ingresos adicionales"""
        if self.has_additional_income:
            if not self.additional_income_amount or self.additional_income_amount <= 0:
                raise ValueError("El monto de ingreso adicional es obligatorio si tiene ingresos adicionales")
            if not self.additional_income_source or not self.additional_income_source.strip():
                raise ValueError("La fuente de ingreso adicional es obligatoria si tiene ingresos adicionales")
        else:
            # Limpiar campos si no tiene ingresos adicionales
            self.additional_income_amount = None
            self.additional_income_source = None
    
    def _clean_and_validate_strings(self) -> None:
        """Limpiar y validar campos de texto"""
        if self.occupation_detail:
            self.occupation_detail = self.occupation_detail.strip()
            if len(self.occupation_detail) > 200:
                raise ValueError("El detalle de ocupación no puede exceder 200 caracteres")
        
        if self.employer_name:
            self.employer_name = self.employer_name.strip()
            if len(self.employer_name) > 150:
                raise ValueError("El nombre del empleador no puede exceder 150 caracteres")
        
        if self.additional_income_source:
            self.additional_income_source = self.additional_income_source.strip()
            if len(self.additional_income_source) > 200:
                raise ValueError("La fuente de ingreso adicional no puede exceder 200 caracteres")
    
    @property
    def total_monthly_income(self) -> Decimal:
        """Ingreso mensual total (principal + adicional)"""
        total = self.monthly_income
        if self.has_additional_income and self.additional_income_amount:
            total += self.additional_income_amount
        return total
    
    @property
    def annual_income(self) -> Decimal:
        """Ingreso anual estimado"""
        return self.total_monthly_income * 12
    
    def is_employed(self) -> bool:
        """Verificar si está empleado"""
        return self.employment_situation in [
            EmploymentSituation.DEPENDENT,
            EmploymentSituation.INDEPENDENT
        ]
    
    def is_formal_worker(self) -> bool:
        """Verificar si es trabajador formal"""
        return self.is_employed() and self.work_condition == WorkCondition.FORMAL
    
    def has_stable_income(self) -> bool:
        """Verificar si tiene ingresos estables (trabajador dependiente formal)"""
        return (
            self.employment_situation == EmploymentSituation.DEPENDENT and
            self.work_condition == WorkCondition.FORMAL
        )
    
    def get_income_level_category(self) -> str:
        """Categorizar nivel de ingresos"""
        total_income = float(self.total_monthly_income)
        
        if total_income <= 1000:
            return "bajo"
        elif total_income <= 3000:
            return "medio"
        elif total_income <= 8000:
            return "alto"
        else:
            return "muy_alto"
    
    def update_income(self, monthly_income: Decimal) -> None:
        """Actualizar ingreso mensual"""
        self.monthly_income = monthly_income
        self._validate_income()
        self.update_timestamp()
    
    def set_additional_income(self, amount: Decimal, source: str) -> None:
        """Establecer ingreso adicional"""
        self.has_additional_income = True
        self.additional_income_amount = amount
        self.additional_income_source = source
        self._validate_additional_income()
        self.update_timestamp()
    
    def remove_additional_income(self) -> None:
        """Remover ingreso adicional"""
        self.has_additional_income = False
        self.additional_income_amount = None
        self.additional_income_source = None
        self.update_timestamp()
    
    def update_employment_info(self, 
                             employment_situation: EmploymentSituation,
                             work_condition: Optional[WorkCondition] = None,
                             occupation_detail: Optional[str] = None,
                             employer_name: Optional[str] = None) -> None:
        """Actualizar información de empleo"""
        self.employment_situation = employment_situation
        self.work_condition = work_condition
        self.occupation_detail = occupation_detail
        self.employer_name = employer_name
        
        self._validate_employment_consistency()
        self._clean_and_validate_strings()
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "employment_situation": self.employment_situation.value,
            "work_condition": self.work_condition.value if self.work_condition else None,
            "occupation_detail": self.occupation_detail,
            "employer_name": self.employer_name,
            "monthly_income": str(self.monthly_income),  # Decimal a string para JSON
            "has_additional_income": self.has_additional_income,
            "additional_income_amount": str(self.additional_income_amount) if self.additional_income_amount else None,
            "additional_income_source": self.additional_income_source,
            "applicant_id": self.applicant_id,
            "is_main_applicant": self.is_main_applicant,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EconomicInfo':
        """Crear instancia desde diccionario"""
        return cls(
            employment_situation=EmploymentSituation(data["employment_situation"]),
            work_condition=WorkCondition(data["work_condition"]) if data.get("work_condition") else None,
            occupation_detail=data.get("occupation_detail"),
            employer_name=data.get("employer_name"),
            monthly_income=Decimal(data["monthly_income"]),
            has_additional_income=data.get("has_additional_income", False),
            additional_income_amount=Decimal(data["additional_income_amount"]) if data.get("additional_income_amount") else None,
            additional_income_source=data.get("additional_income_source"),
            applicant_id=data["applicant_id"],
            is_main_applicant=data.get("is_main_applicant", True)
        )