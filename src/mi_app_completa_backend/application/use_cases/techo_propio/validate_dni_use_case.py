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
        Si la consulta RENIEC es exitosa, el DNI es válido.
        
        Args:
            dto: Datos de validación de DNI
            
        Returns:
            DniValidationResponseDTO: Resultado de la validación
        """
        
        # 1. Validar formato de DNI
        format_validation = self._validate_dni_format(dto.dni)
        if not format_validation.is_valid:
            return DniValidationResponseDTO(
                dni=dto.dni,
                is_valid=False,
                names=None,
                paternal_surname=None,
                maternal_surname=None,
                full_name=None,
                birth_date=None,
                error_message="; ".join(format_validation.validation_errors or []),
                validation_date=datetime.now()
            )
        
        # 2. Consultar RENIEC usando query_document (método correcto)
        try:
            reniec_result = await self.reniec_service.query_document(dto.dni)
            
            # Si la consulta RENIEC es exitosa, el DNI es válido
            if not reniec_result or not reniec_result.success:
                error_msg = reniec_result.message if reniec_result else "DNI no encontrado en RENIEC"
                return DniValidationResponseDTO(
                    dni=dto.dni,
                    is_valid=False,
                    names=None,
                    paternal_surname=None,
                    maternal_surname=None,
                    full_name=None,
                    birth_date=None,
                    error_message=error_msg,
                    validation_date=datetime.now()
                )
            
            # 3. Extraer datos de persona desde la respuesta RENIEC
            dni_data = reniec_result.data
            
            if not dni_data:
                return DniValidationResponseDTO(
                    dni=dto.dni,
                    is_valid=False,
                    names=None,
                    paternal_surname=None,
                    maternal_surname=None,
                    full_name=None,
                    birth_date=None,
                    error_message="No se pudieron obtener datos de RENIEC",
                    validation_date=datetime.now()
                )
            
            # 4. Construir respuesta exitosa con datos de RENIEC
            return DniValidationResponseDTO(
                dni=dni_data.dni,
                is_valid=True,
                names=dni_data.nombres,
                paternal_surname=dni_data.apellido_paterno,
                maternal_surname=dni_data.apellido_materno,
                full_name=dni_data.apellidos,  # Nombre completo desde RENIEC
                birth_date=dni_data.fecha_nacimiento,
                error_message=None,
                validation_date=datetime.now()
            )
            
        except Exception as e:
            return DniValidationResponseDTO(
                dni=dto.dni,
                is_valid=False,
                names=None,
                paternal_surname=None,
                maternal_surname=None,
                full_name=None,
                birth_date=None,
                error_message=f"Error al consultar RENIEC: {str(e)}",
                validation_date=datetime.now()
            )
    
    async def validate_applicant_data(
        self,
        dto: ApplicantValidationDTO
    ) -> DniValidationResponseDTO:
        """
        Validar datos completos de solicitante
        Simplificado: solo valida que el DNI exista en RENIEC
        
        Args:
            dto: Datos del solicitante para validar
            
        Returns:
            DniValidationResponseDTO: Resultado de la validación
        """
        
        # Crear request de validación de DNI simple
        dni_request = DniValidationRequestDTO(dni=dto.document_number)
        
        # Ejecutar validación base (si RENIEC responde, es válido)
        return await self.validate_dni(dni_request)
    
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
                request = DniValidationRequestDTO(dni=dni)
                result = await self.validate_dni(request)
                results[dni] = result
            except Exception as e:
                results[dni] = DniValidationResponseDTO(
                    dni=dni,
                    is_valid=False,
                    names=None,
                    paternal_surname=None,
                    maternal_surname=None,
                    full_name=None,
                    birth_date=None,
                    error_message=f"Error en validación: {str(e)}",
                    validation_date=datetime.now()
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