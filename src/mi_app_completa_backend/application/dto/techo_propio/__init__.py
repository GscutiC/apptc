"""
DTOs para el módulo Techo Propio
"""

from .techo_propio_dto import (
    # DTOs de creación
    ApplicantCreateDTO,
    PropertyInfoCreateDTO,
    HouseholdMemberCreateDTO,
    EconomicInfoCreateDTO,
    TechoPropioApplicationCreateDTO,
    TechoPropioApplicationUpdateDTO,
    
    # DTOs de respuesta
    ApplicantResponseDTO,
    PropertyInfoResponseDTO,
    HouseholdMemberResponseDTO,
    EconomicInfoResponseDTO,
    TechoPropioApplicationResponseDTO,
    
    # DTOs de operaciones específicas
    ApplicationStatusUpdateDTO,
    DniValidationRequestDTO,
    DniValidationResponseDTO,
    ApplicantValidationDTO,
    ApplicationSearchFiltersDTO,
    ApplicationListResponseDTO,
    PaginatedResponseDTO
)

from .ubigeo_validation_dto import (
    UbigeoValidationRequestDTO,
    UbigeoValidationResponseDTO,
    LocationNamesValidationRequestDTO,
    CoordinatesValidationRequestDTO,
    LocationSearchRequestDTO,
    GeographicDataDTO,
    LocationHierarchyDTO,
    DepartmentListDTO,
    ProvinceListDTO,
    DistrictListDTO,
    LocationSearchResultDTO,
    UbigeoStatisticsDTO,
    BulkUbigeoValidationRequestDTO,
    BulkUbigeoValidationResponseDTO
)

# ✅ NUEVOS DTOs de convocatorias
from .convocation_dto import (
    ConvocationCreateDTO,
    ConvocationUpdateDTO,
    ConvocationQueryDTO,
    ConvocationResponseDTO,
    ConvocationListResponseDTO,
    ConvocationStatisticsDTO,
    ConvocationGeneralStatsDTO,
    ConvocationOptionDTO,
    ConvExtendDeadlineDTO,
    ConvBulkOperationDTO,
    ConvBulkOperationResultDTO,
)

__all__ = [
    # DTOs de creación
    'ApplicantCreateDTO',
    'PropertyInfoCreateDTO',
    'HouseholdMemberCreateDTO',
    'EconomicInfoCreateDTO',
    'TechoPropioApplicationCreateDTO',
    'TechoPropioApplicationUpdateDTO',
    
    # DTOs de respuesta
    'ApplicantResponseDTO',
    'PropertyInfoResponseDTO',
    'HouseholdMemberResponseDTO',
    'EconomicInfoResponseDTO',
    'TechoPropioApplicationResponseDTO',
    
    # DTOs de operaciones específicas
    'ApplicationStatusUpdateDTO',
    'DniValidationRequestDTO',
    'DniValidationResponseDTO',
    'ApplicantValidationDTO',
    'ApplicationSearchFiltersDTO',
    'ApplicationListResponseDTO',
    'PaginatedResponseDTO',
    
    # DTOs UBIGEO
    'UbigeoValidationRequestDTO',
    'UbigeoValidationResponseDTO',
    'LocationNamesValidationRequestDTO',
    'CoordinatesValidationRequestDTO',
    'LocationSearchRequestDTO',
    'GeographicDataDTO',
    'LocationHierarchyDTO',
    'DepartmentListDTO',
    'ProvinceListDTO',
    'DistrictListDTO',
    'LocationSearchResultDTO',
    'UbigeoStatisticsDTO',
    'BulkUbigeoValidationRequestDTO',
    'BulkUbigeoValidationResponseDTO',
    
    # ✅ DTOs de convocatorias
    'ConvocationCreateDTO',
    'ConvocationUpdateDTO',
    'ConvocationQueryDTO',
    'ConvocationResponseDTO',
    'ConvocationListResponseDTO',
    'ConvocationStatisticsDTO',
    'ConvocationGeneralStatsDTO',
    'ConvocationOptionDTO',
    'ConvExtendDeadlineDTO',
    'ConvBulkOperationDTO',
    'ConvBulkOperationResultDTO'
]