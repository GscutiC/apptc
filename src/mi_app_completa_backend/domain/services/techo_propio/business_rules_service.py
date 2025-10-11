"""
Servicios de dominio para el módulo Techo Propio
Contiene lógica de negocio compleja que no pertenece a una entidad específica
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
from ...entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, 
    HouseholdMember, EconomicInfo
)
from ...value_objects.techo_propio import (
    ApplicationStatus, DocumentType, CivilStatus, 
    EmploymentSituation, WorkCondition, FamilyRelationship,
    VALIDATION_CONSTANTS
)


class TechoPropioBusinessRules:
    """
    Servicio que implementa las reglas de negocio del programa Techo Propio
    Validaciones complejas que involucran múltiples entidades
    """
    
    @staticmethod
    def validate_eligibility_criteria(application: TechoPropioApplication) -> Tuple[bool, List[str]]:
        """
        Validar criterios de elegibilidad del programa Techo Propio
        Returns: (is_eligible, list_of_errors)
        """
        errors = []
        
        # 1. Validar edad del solicitante principal
        if application.main_applicant:
            age = application.main_applicant.age
            if age < VALIDATION_CONSTANTS["MIN_AGE"]:
                errors.append(f"El solicitante debe tener al menos {VALIDATION_CONSTANTS['MIN_AGE']} años")
            if age > VALIDATION_CONSTANTS["MAX_AGE"]:
                errors.append(f"El solicitante no puede tener más de {VALIDATION_CONSTANTS['MAX_AGE']} años")
        
        # TEMPORALMENTE DESHABILITADO PARA DESARROLLO
        # 2. Validar ingresos familiares (debe estar dentro del rango objetivo)
        # total_income = application.total_family_income
        # per_capita_income = application.per_capita_income
        # 
        # # Límites típicos del programa (estos deberían venir de configuración)
        # MAX_FAMILY_INCOME = Decimal('8000.00')  # Ingreso familiar máximo
        # MAX_PER_CAPITA_INCOME = Decimal('2000.00')  # Ingreso per cápita máximo
        # 
        # if total_income > MAX_FAMILY_INCOME:
        #     errors.append(f"El ingreso familiar total ({total_income}) excede el límite permitido ({MAX_FAMILY_INCOME})")
        # 
        # if per_capita_income > MAX_PER_CAPITA_INCOME:
        #     errors.append(f"El ingreso per cápita ({per_capita_income}) excede el límite permitido ({MAX_PER_CAPITA_INCOME})")
        
        # 3. Validar que no tenga demasiados dependientes (proporción razonable)
        household_size = application.total_household_size
        if household_size > VALIDATION_CONSTANTS["MAX_HOUSEHOLD_MEMBERS"] + 2:  # +2 para solicitante y cónyuge
            errors.append(f"El tamaño del grupo familiar ({household_size}) excede el máximo permitido")
        
        # 4. Validar que tenga al menos información económica básica
        if not application.main_applicant_economic:
            errors.append("La información económica del solicitante principal es obligatoria")
        
        # 5. Si tiene cónyuge, debe tener información económica del cónyuge
        if application.spouse and not application.spouse_economic:
            errors.append("La información económica del cónyuge es obligatoria")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def calculate_priority_score(application: TechoPropioApplication) -> int:
        """
        Calcular puntaje de prioridad para la solicitud
        Mayor puntaje = mayor prioridad
        """
        score = 0
        
        if not application.main_applicant or not application.main_applicant_economic:
            return 0
        
        # 1. Puntaje por ingresos (menos ingresos = más puntaje)
        per_capita_income = float(application.per_capita_income)
        if per_capita_income <= 500:
            score += 30
        elif per_capita_income <= 1000:
            score += 20
        elif per_capita_income <= 1500:
            score += 10
        
        # 2. Puntaje por tamaño de familia (familias más grandes = más puntaje)
        household_size = application.total_household_size
        if household_size >= 6:
            score += 25
        elif household_size >= 4:
            score += 15
        elif household_size >= 3:
            score += 10
        
        # 3. Puntaje por discapacidad
        if application.main_applicant.has_disability():
            score += 20
        if application.spouse and application.spouse.has_disability():
            score += 15
        
        # Verificar discapacidad en carga familiar
        disabled_members = sum(1 for member in application.household_members if member.has_disability())
        score += disabled_members * 10
        
        # 4. Puntaje por menores de edad
        minors = sum(1 for member in application.household_members if member.is_minor())
        score += minors * 8
        
        # 5. Puntaje por situación laboral
        if application.main_applicant_economic.employment_situation == EmploymentSituation.UNEMPLOYED:
            score += 15
        elif (application.main_applicant_economic.employment_situation == EmploymentSituation.INDEPENDENT and
              application.main_applicant_economic.work_condition == WorkCondition.INFORMAL):
            score += 10
        
        # 6. Puntaje por jefe de hogar mujer soltera con hijos
        if (application.main_applicant.civil_status == CivilStatus.SINGLE and 
            not application.spouse and 
            len(application.household_members) > 0):
            # Asumiendo que se puede inferir género o se agregará después
            score += 20
        
        return max(0, min(score, 100))  # Normalizar entre 0-100
    
    @staticmethod
    def validate_dni_uniqueness(applications: List[TechoPropioApplication], new_application: TechoPropioApplication) -> List[str]:
        """
        Validar que los DNIs en la nueva solicitud no estén duplicados en otras solicitudes activas
        """
        errors = []
        new_dnis = set()
        
        # Recopilar DNIs de la nueva solicitud
        if new_application.main_applicant:
            new_dnis.add(new_application.main_applicant.document_number)
        if new_application.spouse:
            new_dnis.add(new_application.spouse.document_number)
        for member in new_application.household_members:
            new_dnis.add(member.document_number)
        
        # Verificar contra solicitudes existentes (excluyendo estados finales como rechazado)
        active_statuses = [
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
            ApplicationStatus.APPROVED
        ]
        
        for existing_app in applications:
            if (existing_app.id != new_application.id and 
                existing_app.status in active_statuses):
                
                existing_dnis = set()
                if existing_app.main_applicant:
                    existing_dnis.add(existing_app.main_applicant.document_number)
                if existing_app.spouse:
                    existing_dnis.add(existing_app.spouse.document_number)
                for member in existing_app.household_members:
                    existing_dnis.add(member.document_number)
                
                # Encontrar duplicados
                duplicates = new_dnis.intersection(existing_dnis)
                for dni in duplicates:
                    errors.append(f"El DNI {dni} ya está registrado en otra solicitud activa (Nº {existing_app.application_number})")
        
        return errors
    
    @staticmethod
    def recommend_next_steps(application: TechoPropioApplication) -> List[str]:
        """
        Recomendar próximos pasos basados en el estado actual de la solicitud
        """
        recommendations = []
        
        if application.status == ApplicationStatus.DRAFT:
            completion = application.get_completion_percentage()
            
            if not application.main_applicant:
                recommendations.append("Completar información del solicitante principal")
            elif not application.main_applicant.reniec_validated:
                recommendations.append("Validar DNI del solicitante principal con RENIEC")
            
            if not application.property_info:
                recommendations.append("Completar información del predio")
            elif not application.property_info.ubigeo_validated:
                recommendations.append("Validar ubicación del predio")
            
            if not application.main_applicant_economic:
                recommendations.append("Completar información económica del solicitante")
            
            if (application.main_applicant and 
                application.main_applicant.is_married_or_cohabiting() and 
                not application.spouse):
                recommendations.append("Agregar información del cónyuge/conviviente")
            
            if application.spouse and not application.spouse_economic:
                recommendations.append("Completar información económica del cónyuge")
            
            if completion >= 80:
                recommendations.append("La solicitud está casi completa. Revise y envíe para evaluación.")
            
        elif application.status == ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
            recommendations.append("Revisar comentarios del evaluador y proporcionar información solicitada")
            if application.reviewer_comments:
                recommendations.append(f"Comentarios: {application.reviewer_comments}")
        
        elif application.status == ApplicationStatus.SUBMITTED:
            recommendations.append("Su solicitud está en cola de evaluación")
            recommendations.append("Tiempo estimado de evaluación: 15-30 días hábiles")
        
        elif application.status == ApplicationStatus.UNDER_REVIEW:
            recommendations.append("Su solicitud está siendo evaluada")
            recommendations.append("Manténgase atento a posibles solicitudes de información adicional")
        
        return recommendations
    
    @staticmethod
    def validate_family_consistency(application: TechoPropioApplication) -> List[str]:
        """
        Validar consistencia lógica de la información familiar
        """
        errors = []
        
        if not application.main_applicant:
            return ["Solicitante principal es obligatorio"]
        
        # 1. Validar edades lógicas
        main_age = application.main_applicant.age
        
        if application.spouse:
            spouse_age = application.spouse.age
            age_diff = abs(main_age - spouse_age)
            if age_diff > 25:  # Diferencia de edad muy grande
                errors.append(f"Diferencia de edad entre cónyuges muy grande ({age_diff} años)")
        
        # 2. Validar relaciones familiares lógicas
        for member in application.household_members:
            member_age = member.age
            
            if member.relationship == FamilyRelationship.CHILD:
                min_parent_age = member_age + 15  # Padre mínimo 15 años mayor que hijo
                if main_age < min_parent_age:
                    errors.append(f"Edad del solicitante ({main_age}) inconsistente con hijo de {member_age} años")
                
                if member_age > 25 and not member.is_dependent:
                    # Hijo mayor independiente podría no ser elegible como dependiente
                    pass  # Solo advertencia, no error
            
            elif member.relationship == FamilyRelationship.PARENT:
                min_child_age = main_age + 15  # Hijo debe ser al menos 15 años menor que padre
                if member_age < min_child_age:
                    errors.append(f"Edad del padre/madre ({member_age}) inconsistente con solicitante de {main_age} años")
        
        # 3. Validar cantidad de cónyuges
        spouse_count = sum(1 for member in application.household_members 
                          if member.relationship in [FamilyRelationship.SPOUSE, FamilyRelationship.PARTNER])
        if application.spouse and spouse_count > 0:
            errors.append("No se puede tener cónyuge registrado y también en la carga familiar")
        elif spouse_count > 1:
            errors.append("No se puede tener más de un cónyuge/conviviente")
        
        return errors


class TechoPropioStatisticsService:
    """
    Servicio para generar estadísticas y reportes del módulo Techo Propio
    """
    
    @staticmethod
    def generate_application_summary(applications: List[TechoPropioApplication]) -> Dict[str, Any]:
        """
        Generar resumen estadístico de solicitudes
        """
        if not applications:
            return {"total": 0, "by_status": {}, "by_department": {}}
        
        summary = {
            "total": len(applications),
            "by_status": {},
            "by_department": {},
            "by_income_range": {},
            "average_household_size": 0,
            "total_beneficiaries": 0,
            "priority_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        total_household_size = 0
        total_beneficiaries = 0
        
        for app in applications:
            # Por estado
            status = app.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Por departamento
            if app.property_info:
                dept = app.property_info.department
                summary["by_department"][dept] = summary["by_department"].get(dept, 0) + 1
            
            # Por rango de ingresos
            income = float(app.per_capita_income)
            if income <= 500:
                range_key = "0-500"
            elif income <= 1000:
                range_key = "500-1000"
            elif income <= 1500:
                range_key = "1000-1500"
            else:
                range_key = "1500+"
            
            summary["by_income_range"][range_key] = summary["by_income_range"].get(range_key, 0) + 1
            
            # Tamaño promedio de hogar
            household_size = app.total_household_size
            total_household_size += household_size
            total_beneficiaries += household_size
            
            # Distribución de prioridades
            priority_score = TechoPropioBusinessRules.calculate_priority_score(app)
            if priority_score >= 70:
                summary["priority_distribution"]["high"] += 1
            elif priority_score >= 40:
                summary["priority_distribution"]["medium"] += 1
            else:
                summary["priority_distribution"]["low"] += 1
        
        summary["average_household_size"] = round(total_household_size / len(applications), 2)
        summary["total_beneficiaries"] = total_beneficiaries
        
        return summary