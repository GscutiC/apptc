"""
Caso de uso para validación de DNI con integración RENIEC
Proporciona validación automática de identidad para solicitudes Techo Propio
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date

# Importar servicios existentes
from ....infrastructure.services.government_apis.reniec_service import ReniecService

# Importar DTOs
from ...dto.techo_propio import (
    DniValidationRequestDTO,
    DniValidationResponseDTO,
    ApplicantValidationDTO
)


@dataclass
class DniValidationResult:
    """Resultado de validación de DNI"""
    is_valid: bool
    person_data: Optional[Dict[str, Any]] = None
    validation_errors: Optional[list] = None
    reniec_response: Optional[Dict[str, Any]] = None


class ValidateDniUseCase:
    """
    Caso de uso para validar DNI usando el servicio RENIEC
    Integra con el servicio existente y proporciona validaciones específicas para Techo Propio
    """
    
    def __init__(self, reniec_service: ReniecService):
        self.reniec_service = reniec_service
    
    async def validate_dni(
        self,
        dto: DniValidationRequestDTO
    ) -> DniValidationResponseDTO:
        """
        Validar DNI completo con RENIEC
        
        Args:
            dto: Datos de validación de DNI
            
        Returns:
            DniValidationResponseDTO: Resultado de la validación
        """
        
        # 1. Validar formato de DNI
        format_validation = self._validate_dni_format(dto.document_number)
        if not format_validation.is_valid:
            return DniValidationResponseDTO(
                document_number=dto.document_number,
                is_valid=False,
                validation_errors=format_validation.validation_errors,
                person_data=None,
                validated_at=datetime.now()
            )
        
        # 2. Consultar RENIEC
        try:
            reniec_result = await self.reniec_service.validate_person(dto.document_number)
            
            if not reniec_result or not reniec_result.get('success', False):
                return DniValidationResponseDTO(
                    document_number=dto.document_number,
                    is_valid=False,
                    validation_errors=["DNI no encontrado en RENIEC"],
                    person_data=None,
                    validated_at=datetime.now()
                )
            
            # 3. Extraer datos de persona
            person_data = self._extract_person_data(reniec_result)
            
            # 4. Validar datos específicos si se proporcionan
            validation_errors = []
            if dto.expected_first_name or dto.expected_paternal_surname:
                name_validation = self._validate_expected_names(person_data, dto)
                if not name_validation.is_valid:
                    validation_errors.extend(name_validation.validation_errors)
            
            # 5. Validar edad para Techo Propio
            age_validation = self._validate_age_for_program(person_data)
            if not age_validation.is_valid:
                validation_errors.extend(age_validation.validation_errors)
            
            return DniValidationResponseDTO(
                document_number=dto.document_number,
                is_valid=len(validation_errors) == 0,
                validation_errors=validation_errors if validation_errors else None,
                person_data=person_data,
                validated_at=datetime.now()
            )
            
        except Exception as e:
            return DniValidationResponseDTO(
                document_number=dto.document_number,
                is_valid=False,
                validation_errors=[f"Error al consultar RENIEC: {str(e)}"],
                person_data=None,
                validated_at=datetime.now()
            )
    
    async def validate_applicant_data(
        self,
        dto: ApplicantValidationDTO
    ) -> DniValidationResponseDTO:
        """
        Validar datos completos de solicitante
        
        Args:
            dto: Datos del solicitante para validar
            
        Returns:
            DniValidationResponseDTO: Resultado de la validación
        """
        
        # Crear request de validación de DNI
        dni_request = DniValidationRequestDTO(
            document_number=dto.document_number,
            expected_first_name=dto.first_name,
            expected_paternal_surname=dto.paternal_surname,
            expected_maternal_surname=dto.maternal_surname
        )
        
        # Ejecutar validación base
        base_result = await self.validate_dni(dni_request)
        
        # Si la validación base falló, retornar resultado
        if not base_result.is_valid:
            return base_result
        
        # Validaciones adicionales para solicitante
        additional_errors = []
        
        # Validar apellido materno si se proporciona
        if dto.maternal_surname and base_result.person_data:
            maternal_surname_reniec = base_result.person_data.get('maternal_surname', '').upper()
            maternal_surname_provided = dto.maternal_surname.upper()
            
            if maternal_surname_reniec != maternal_surname_provided:
                additional_errors.append(
                    f"Apellido materno no coincide. RENIEC: '{maternal_surname_reniec}', "
                    f"Proporcionado: '{maternal_surname_provided}'"
                )
        
        # Validar fecha de nacimiento si se proporciona
        if dto.birth_date and base_result.person_data:
            birth_date_validation = self._validate_birth_date(
                base_result.person_data.get('birth_date'),
                dto.birth_date
            )
            if not birth_date_validation.is_valid:
                additional_errors.extend(birth_date_validation.validation_errors)
        
        # Combinar errores
        all_errors = (base_result.validation_errors or []) + additional_errors
        
        return DniValidationResponseDTO(
            document_number=dto.document_number,
            is_valid=len(all_errors) == 0,
            validation_errors=all_errors if all_errors else None,
            person_data=base_result.person_data,
            validated_at=datetime.now()
        )
    
    async def batch_validate_dnis(
        self,
        document_numbers: list[str]
    ) -> Dict[str, DniValidationResponseDTO]:
        """
        Validar múltiples DNIs en lote
        
        Args:
            document_numbers: Lista de números de DNI
            
        Returns:
            Dict con resultados de validación por DNI
        """
        
        results = {}
        
        for dni in document_numbers:
            try:
                request = DniValidationRequestDTO(document_number=dni)
                result = await self.validate_dni(request)
                results[dni] = result
            except Exception as e:
                results[dni] = DniValidationResponseDTO(
                    document_number=dni,
                    is_valid=False,
                    validation_errors=[f"Error en validación: {str(e)}"],
                    person_data=None,
                    validated_at=datetime.now()
                )
        
        return results
    
    def _validate_dni_format(self, document_number: str) -> DniValidationResult:
        """Validar formato de DNI"""
        errors = []
        
        # Validar longitud
        if len(document_number) != 8:
            errors.append("El DNI debe tener exactamente 8 dígitos")
        
        # Validar que solo contenga números
        if not document_number.isdigit():
            errors.append("El DNI debe contener solo números")
        
        # Validar que no sean todos ceros o números repetidos
        if document_number == "00000000" or len(set(document_number)) == 1:
            errors.append("DNI inválido: no puede ser todos ceros o números repetidos")
        
        return DniValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors if errors else None
        )
    
    def _extract_person_data(self, reniec_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer datos de persona desde respuesta RENIEC"""
        data = reniec_result.get('data', {})
        
        return {
            'first_name': data.get('nombres', '').strip(),
            'paternal_surname': data.get('apellido_paterno', '').strip(),
            'maternal_surname': data.get('apellido_materno', '').strip(),
            'birth_date': data.get('fecha_nacimiento'),
            'full_name': f"{data.get('nombres', '')} {data.get('apellido_paterno', '')} {data.get('apellido_materno', '')}".strip(),
            'ubigeo_birth': data.get('ubigeo_nacimiento'),
            'birth_place': data.get('lugar_nacimiento', ''),
            'sex': data.get('sexo', ''),
            'civil_status': data.get('estado_civil', ''),
            'address': data.get('direccion', ''),
            'restriction': data.get('restriccion', ''),
            'photo_url': data.get('foto', ''),
            'verified_at': datetime.now().isoformat()
        }
    
    def _validate_expected_names(
        self, 
        person_data: Dict[str, Any], 
        dto: DniValidationRequestDTO
    ) -> DniValidationResult:
        """Validar nombres esperados contra datos RENIEC"""
        errors = []
        
        # Normalizar datos para comparación
        reniec_first_name = person_data.get('first_name', '').upper().strip()
        reniec_paternal = person_data.get('paternal_surname', '').upper().strip()
        reniec_maternal = person_data.get('maternal_surname', '').upper().strip()
        
        # Validar nombre
        if dto.expected_first_name:
            expected_first_name = dto.expected_first_name.upper().strip()
            if reniec_first_name != expected_first_name:
                errors.append(
                    f"Nombre no coincide. RENIEC: '{reniec_first_name}', "
                    f"Esperado: '{expected_first_name}'"
                )
        
        # Validar apellido paterno
        if dto.expected_paternal_surname:
            expected_paternal = dto.expected_paternal_surname.upper().strip()
            if reniec_paternal != expected_paternal:
                errors.append(
                    f"Apellido paterno no coincide. RENIEC: '{reniec_paternal}', "
                    f"Esperado: '{expected_paternal}'"
                )
        
        # Validar apellido materno
        if dto.expected_maternal_surname:
            expected_maternal = dto.expected_maternal_surname.upper().strip()
            if reniec_maternal != expected_maternal:
                errors.append(
                    f"Apellido materno no coincide. RENIEC: '{reniec_maternal}', "
                    f"Esperado: '{expected_maternal}'"
                )
        
        return DniValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors if errors else None
        )
    
    def _validate_age_for_program(self, person_data: Dict[str, Any]) -> DniValidationResult:
        """Validar edad para programa Techo Propio"""
        errors = []
        
        birth_date_str = person_data.get('birth_date')
        if not birth_date_str:
            errors.append("Fecha de nacimiento no disponible en RENIEC")
            return DniValidationResult(is_valid=False, validation_errors=errors)
        
        try:
            # Parsear fecha de nacimiento (formato puede variar)
            if isinstance(birth_date_str, str):
                # Intentar diferentes formatos de fecha
                birth_date = None
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        birth_date = datetime.strptime(birth_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not birth_date:
                    errors.append(f"Formato de fecha de nacimiento inválido: {birth_date_str}")
                    return DniValidationResult(is_valid=False, validation_errors=errors)
            else:
                birth_date = birth_date_str
            
            # Calcular edad
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            # Validar rango de edad para Techo Propio (típicamente 18-65 años)
            if age < 18:
                errors.append(f"Solicitante menor de edad: {age} años. Debe ser mayor de 18 años")
            elif age > 70:
                errors.append(f"Solicitante con edad avanzada: {age} años. Verificar elegibilidad")
            
        except Exception as e:
            errors.append(f"Error al calcular edad: {str(e)}")
        
        return DniValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors if errors else None
        )
    
    def _validate_birth_date(
        self, 
        reniec_birth_date: Any, 
        provided_birth_date: date
    ) -> DniValidationResult:
        """Validar fecha de nacimiento proporcionada contra RENIEC"""
        errors = []
        
        if not reniec_birth_date:
            errors.append("Fecha de nacimiento no disponible en RENIEC")
            return DniValidationResult(is_valid=False, validation_errors=errors)
        
        try:
            # Convertir fecha RENIEC a date si es string
            if isinstance(reniec_birth_date, str):
                reniec_date = None
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        reniec_date = datetime.strptime(reniec_birth_date, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not reniec_date:
                    errors.append(f"Formato de fecha RENIEC inválido: {reniec_birth_date}")
                    return DniValidationResult(is_valid=False, validation_errors=errors)
            else:
                reniec_date = reniec_birth_date
            
            # Comparar fechas
            if reniec_date != provided_birth_date:
                errors.append(
                    f"Fecha de nacimiento no coincide. RENIEC: {reniec_date}, "
                    f"Proporcionada: {provided_birth_date}"
                )
            
        except Exception as e:
            errors.append(f"Error al validar fecha de nacimiento: {str(e)}")
        
        return DniValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors if errors else None
        )