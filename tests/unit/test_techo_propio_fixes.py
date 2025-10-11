"""
Tests para verificar las correcciones del módulo Techo Propio
Ejecutar después de aplicar los fixes

Uso:
    pytest tests/unit/test_techo_propio_fixes.py -v
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.mi_app_completa_backend.domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, 
    HouseholdMember, EconomicInfo
)
from src.mi_app_completa_backend.domain.value_objects.techo_propio import (
    DocumentType, CivilStatus, EducationLevel, DisabilityType,
    EmploymentSituation, WorkCondition, FamilyRelationship, ApplicationStatus
)


# ============================================================================
# TESTS PARA FIX #1: Campo address en PropertyInfo
# ============================================================================

class TestPropertyInfoAddressField:
    """Tests para verificar el campo address en PropertyInfo"""
    
    def test_property_info_with_address_success(self):
        """✅ PropertyInfo debe crearse correctamente con address"""
        property_info = PropertyInfo(
            department="Lima",
            province="Lima",
            district="San Juan de Lurigancho",
            lote="10",
            address="Av. Principal 123",  # ✅ Campo address
            ubigeo_code="150101",
            manzana="A",
            populated_center="Canto Grande"
        )
        
        assert property_info.address == "Av. Principal 123"
        assert property_info.department == "Lima"
        assert property_info.lote == "10"
    
    def test_property_info_without_address_fails(self):
        """❌ PropertyInfo debe fallar sin address"""
        with pytest.raises(TypeError) as exc_info:
            PropertyInfo(
                department="Lima",
                province="Lima",
                district="San Juan de Lurigancho",
                lote="10",
                # ❌ Sin address - debe fallar
                ubigeo_code="150101"
            )
        
        assert "address" in str(exc_info.value).lower()
    
    def test_property_info_empty_address_fails(self):
        """❌ PropertyInfo debe fallar con address vacío"""
        with pytest.raises(ValueError) as exc_info:
            PropertyInfo(
                department="Lima",
                province="Lima",
                district="San Juan de Lurigancho",
                lote="10",
                address="",  # ❌ Vacío - debe fallar
                ubigeo_code="150101"
            )
        
        assert "dirección" in str(exc_info.value).lower()


# ============================================================================
# TESTS PARA FIX #2: Campos nuevos en HouseholdMember
# ============================================================================

class TestHouseholdMemberNewFields:
    """Tests para verificar los campos nuevos en HouseholdMember"""
    
    def test_household_member_with_all_new_fields_success(self):
        """✅ HouseholdMember debe crearse con todos los campos nuevos"""
        member = HouseholdMember(
            first_name="Carlos",
            paternal_surname="Pérez",
            maternal_surname="García",
            document_type=DocumentType.DNI,
            document_number="12345678",
            birth_date=date(2005, 5, 15),
            civil_status=CivilStatus.SINGLE,  # ✅ Campo nuevo
            education_level=EducationLevel.SECONDARY_COMPLETE,
            occupation="Estudiante",  # ✅ Campo nuevo
            employment_situation=EmploymentSituation.UNEMPLOYED,  # ✅ Campo nuevo
            work_condition=WorkCondition.INFORMAL,  # ✅ Campo nuevo
            monthly_income=Decimal("0.00"),  # ✅ Campo nuevo
            disability_type=DisabilityType.NONE,
            relationship=FamilyRelationship.CHILD,
            is_dependent=True
        )
        
        assert member.civil_status == CivilStatus.SINGLE
        assert member.occupation == "Estudiante"
        assert member.employment_situation == EmploymentSituation.UNEMPLOYED
        assert member.work_condition == WorkCondition.INFORMAL
        assert member.monthly_income == Decimal("0.00")
    
    def test_household_member_without_civil_status_fails(self):
        """❌ HouseholdMember debe fallar sin civil_status"""
        with pytest.raises(TypeError) as exc_info:
            HouseholdMember(
                first_name="Carlos",
                paternal_surname="Pérez",
                maternal_surname="García",
                document_type=DocumentType.DNI,
                document_number="12345678",
                birth_date=date(2005, 5, 15),
                # ❌ Sin civil_status
                education_level=EducationLevel.SECONDARY_COMPLETE,
                occupation="Estudiante",
                employment_situation=EmploymentSituation.UNEMPLOYED,
                work_condition=WorkCondition.INFORMAL,
                monthly_income=Decimal("0.00"),
                disability_type=DisabilityType.NONE,
                is_dependent=True
            )
        
        assert "civil_status" in str(exc_info.value)
    
    def test_household_member_without_occupation_fails(self):
        """❌ HouseholdMember debe fallar sin occupation"""
        with pytest.raises(TypeError) as exc_info:
            HouseholdMember(
                first_name="Carlos",
                paternal_surname="Pérez",
                maternal_surname="García",
                document_type=DocumentType.DNI,
                document_number="12345678",
                birth_date=date(2005, 5, 15),
                civil_status=CivilStatus.SINGLE,
                education_level=EducationLevel.SECONDARY_COMPLETE,
                # ❌ Sin occupation
                employment_situation=EmploymentSituation.UNEMPLOYED,
                work_condition=WorkCondition.INFORMAL,
                monthly_income=Decimal("0.00"),
                disability_type=DisabilityType.NONE,
                is_dependent=True
            )
        
        assert "occupation" in str(exc_info.value)
    
    def test_household_member_without_employment_situation_fails(self):
        """❌ HouseholdMember debe fallar sin employment_situation"""
        with pytest.raises(TypeError) as exc_info:
            HouseholdMember(
                first_name="Carlos",
                paternal_surname="Pérez",
                maternal_surname="García",
                document_type=DocumentType.DNI,
                document_number="12345678",
                birth_date=date(2005, 5, 15),
                civil_status=CivilStatus.SINGLE,
                education_level=EducationLevel.SECONDARY_COMPLETE,
                occupation="Estudiante",
                # ❌ Sin employment_situation
                work_condition=WorkCondition.INFORMAL,
                monthly_income=Decimal("0.00"),
                disability_type=DisabilityType.NONE,
                is_dependent=True
            )
        
        assert "employment_situation" in str(exc_info.value)
    
    def test_household_member_with_optional_relationship(self):
        """✅ HouseholdMember puede crearse sin relationship (es opcional)"""
        member = HouseholdMember(
            first_name="Carlos",
            paternal_surname="Pérez",
            maternal_surname="García",
            document_type=DocumentType.DNI,
            document_number="12345678",
            birth_date=date(2005, 5, 15),
            civil_status=CivilStatus.SINGLE,
            education_level=EducationLevel.SECONDARY_COMPLETE,
            occupation="Estudiante",
            employment_situation=EmploymentSituation.UNEMPLOYED,
            work_condition=WorkCondition.INFORMAL,
            monthly_income=Decimal("0.00"),
            disability_type=DisabilityType.NONE,
            relationship=None,  # ✅ Opcional
            is_dependent=True
        )
        
        assert member.relationship is None
        assert member.first_name == "Carlos"


# ============================================================================
# TESTS DE INTEGRACIÓN: Aplicación Completa
# ============================================================================

class TestCompleteApplicationFlow:
    """Tests de integración para verificar flujo completo"""
    
    @pytest.fixture
    def sample_applicant(self):
        """Crear solicitante de prueba"""
        return Applicant(
            document_type=DocumentType.DNI,
            document_number="12345678",
            first_name="Juan",
            paternal_surname="Pérez",
            maternal_surname="García",
            birth_date=date(1985, 5, 15),
            civil_status=CivilStatus.MARRIED,
            education_level=EducationLevel.UNIVERSITY_COMPLETE,
            occupation="Ingeniero",
            disability_type=DisabilityType.NONE,
            is_main_applicant=True,
            phone_number="987654321",
            email="juan@example.com"
        )
    
    @pytest.fixture
    def sample_property_with_address(self):
        """Crear propiedad de prueba con address"""
        return PropertyInfo(
            department="Lima",
            province="Lima",
            district="San Juan de Lurigancho",
            lote="10",
            address="Av. Principal 123, Canto Grande",  # ✅ Con address
            ubigeo_code="150101",
            manzana="A",
            populated_center="Canto Grande"
        )
    
    @pytest.fixture
    def sample_economic_info(self):
        """Crear información económica de prueba"""
        return EconomicInfo(
            employment_situation=EmploymentSituation.DEPENDENT,
            monthly_income=Decimal("3000.00"),
            applicant_id="test-id",
            work_condition=WorkCondition.FORMAL,
            occupation_detail="Ingeniero de Sistemas",
            employer_name="TechCorp SAC",
            has_additional_income=False,
            is_main_applicant=True
        )
    
    @pytest.fixture
    def sample_household_member_with_new_fields(self):
        """Crear miembro del hogar con campos nuevos"""
        return HouseholdMember(
            first_name="Carlos",
            paternal_surname="Pérez",
            maternal_surname="García",
            document_type=DocumentType.DNI,
            document_number="87654321",
            birth_date=date(2005, 3, 10),
            civil_status=CivilStatus.SINGLE,  # ✅ Campo nuevo
            education_level=EducationLevel.SECONDARY_COMPLETE,
            occupation="Estudiante",  # ✅ Campo nuevo
            employment_situation=EmploymentSituation.UNEMPLOYED,  # ✅ Campo nuevo
            work_condition=WorkCondition.INFORMAL,  # ✅ Campo nuevo
            monthly_income=Decimal("0.00"),  # ✅ Campo nuevo
            disability_type=DisabilityType.NONE,
            relationship=FamilyRelationship.CHILD,
            is_dependent=True
        )
    
    def test_create_complete_application_with_fixes(
        self,
        sample_applicant,
        sample_property_with_address,
        sample_economic_info,
        sample_household_member_with_new_fields
    ):
        """✅ Crear solicitud completa con todos los fixes aplicados"""
        
        # Crear aplicación
        application = TechoPropioApplication(
            status=ApplicationStatus.DRAFT,
            main_applicant=sample_applicant,
            property_info=sample_property_with_address,  # ✅ Con address
            household_members=[sample_household_member_with_new_fields],  # ✅ Con campos nuevos
            main_applicant_economic=sample_economic_info,
            user_id="user-test-id",
            created_by="user-test-id"
        )
        
        # Verificaciones
        assert application.main_applicant is not None
        assert application.property_info.address == "Av. Principal 123, Canto Grande"  # ✅ address presente
        assert len(application.household_members) == 1
        
        # Verificar campos nuevos del miembro
        member = application.household_members[0]
        assert member.civil_status == CivilStatus.SINGLE
        assert member.occupation == "Estudiante"
        assert member.employment_situation == EmploymentSituation.UNEMPLOYED
        assert member.work_condition == WorkCondition.INFORMAL
        assert member.monthly_income == Decimal("0.00")
        
        # Verificar cálculos
        assert application.total_household_size == 2  # Solicitante + 1 miembro
        assert application.total_family_income > Decimal("0")
        assert application.get_completion_percentage() > 0


# ============================================================================
# TESTS DE VALIDACIÓN
# ============================================================================

class TestValidations:
    """Tests para verificar validaciones correctas"""
    
    def test_property_address_cannot_be_empty(self):
        """❌ Address no puede estar vacío"""
        with pytest.raises(ValueError):
            PropertyInfo(
                department="Lima",
                province="Lima",
                district="San Juan de Lurigancho",
                lote="10",
                address="   ",  # Solo espacios - debe fallar
                ubigeo_code="150101"
            )
    
    def test_household_member_occupation_cannot_be_empty(self):
        """❌ Occupation no puede estar vacío"""
        with pytest.raises(ValueError):
            HouseholdMember(
                first_name="Carlos",
                paternal_surname="Pérez",
                maternal_surname="García",
                document_type=DocumentType.DNI,
                document_number="12345678",
                birth_date=date(2005, 5, 15),
                civil_status=CivilStatus.SINGLE,
                education_level=EducationLevel.SECONDARY_COMPLETE,
                occupation="",  # Vacío - debe fallar
                employment_situation=EmploymentSituation.UNEMPLOYED,
                work_condition=WorkCondition.INFORMAL,
                monthly_income=Decimal("0.00"),
                disability_type=DisabilityType.NONE,
                is_dependent=True
            )
    
    def test_household_member_monthly_income_must_be_positive_or_zero(self):
        """❌ monthly_income no puede ser negativo"""
        with pytest.raises(ValueError):
            HouseholdMember(
                first_name="Carlos",
                paternal_surname="Pérez",
                maternal_surname="García",
                document_type=DocumentType.DNI,
                document_number="12345678",
                birth_date=date(2005, 5, 15),
                civil_status=CivilStatus.SINGLE,
                education_level=EducationLevel.SECONDARY_COMPLETE,
                occupation="Estudiante",
                employment_situation=EmploymentSituation.UNEMPLOYED,
                work_condition=WorkCondition.INFORMAL,
                monthly_income=Decimal("-100.00"),  # Negativo - debe fallar
                disability_type=DisabilityType.NONE,
                is_dependent=True
            )


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture
def mock_user_id():
    """User ID de prueba"""
    return "user_test_123"


# ============================================================================
# MARK PARA EJECUCIÓN SELECTIVA
# ============================================================================

pytestmark = pytest.mark.techo_propio_fixes
