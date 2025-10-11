"""
Script de corrección automática para el módulo Techo Propio
Aplica todos los fixes identificados en el diagnóstico

Uso:
    python scripts/fix_techo_propio_module.py --dry-run  # Ver cambios sin aplicar
    python scripts/fix_techo_propio_module.py --apply    # Aplicar cambios
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

# ============================================================================
# FIX #1: Agregar campo address en PropertyInfo
# ============================================================================

def fix_property_address(dry_run: bool = True) -> bool:
    """Fix #1: Agregar campo address en create_application_use_case.py"""
    
    file_path = Path("src/mi_app_completa_backend/application/use_cases/techo_propio/create_application_use_case.py")
    
    if not file_path.exists():
        print_error(f"Archivo no encontrado: {file_path}")
        return False
    
    print_info(f"Procesando FIX #1: Campo address en PropertyInfo")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el bloque de creación de PropertyInfo
    old_code = """        # Crear información del predio
        property_info = PropertyInfo(
            department=dto.property_info.department,
            province=dto.property_info.province,
            district=dto.property_info.district,
            lote=dto.property_info.lote,
            ubigeo_code=dto.property_info.ubigeo_code,"""
    
    new_code = """        # Crear información del predio
        property_info = PropertyInfo(
            department=dto.property_info.department,
            province=dto.property_info.province,
            district=dto.property_info.district,
            lote=dto.property_info.lote,
            address=dto.property_info.address,  # ✅ FIX: Campo agregado
            ubigeo_code=dto.property_info.ubigeo_code,"""
    
    if old_code in content:
        if not dry_run:
            content = content.replace(old_code, new_code)
            
            # Crear backup
            backup_path = file_path.with_suffix(f'.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(file_path, backup_path)
            print_info(f"Backup creado: {backup_path}")
            
            # Escribir archivo corregido
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_success("Campo 'address' agregado en PropertyInfo")
        else:
            print_warning("DRY-RUN: Campo 'address' sería agregado en PropertyInfo")
        return True
    else:
        print_warning("Código no encontrado o ya fue aplicado el fix")
        return False

# ============================================================================
# FIX #2: Agregar campos nuevos en HouseholdMember
# ============================================================================

def fix_household_member_fields(dry_run: bool = True) -> bool:
    """Fix #2: Agregar campos nuevos en HouseholdMember"""
    
    file_path = Path("src/mi_app_completa_backend/application/use_cases/techo_propio/create_application_use_case.py")
    
    if not file_path.exists():
        print_error(f"Archivo no encontrado: {file_path}")
        return False
    
    print_info(f"Procesando FIX #2: Campos nuevos en HouseholdMember")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el bloque de creación de HouseholdMember
    old_code = """        # Crear miembros de carga familiar
        household_members = []
        for member_dto in dto.household_members:
            member = HouseholdMember(
                first_name=member_dto.first_name,
                paternal_surname=member_dto.paternal_surname,
                maternal_surname=member_dto.maternal_surname,
                document_type=member_dto.document_type,
                document_number=member_dto.document_number,
                birth_date=member_dto.birth_date,
                relationship=member_dto.relationship,
                education_level=member_dto.education_level,
                disability_type=member_dto.disability_type,
                is_dependent=member_dto.is_dependent
            )
            household_members.append(member)"""
    
    new_code = """        # Crear miembros de carga familiar
        household_members = []
        for member_dto in dto.household_members:
            member = HouseholdMember(
                first_name=member_dto.first_name,
                paternal_surname=member_dto.paternal_surname,
                maternal_surname=member_dto.maternal_surname,
                document_type=member_dto.document_type,
                document_number=member_dto.document_number,
                birth_date=member_dto.birth_date,
                civil_status=member_dto.civil_status,  # ✅ FIX: Campo agregado
                education_level=member_dto.education_level,
                occupation=member_dto.occupation,  # ✅ FIX: Campo agregado
                employment_situation=member_dto.employment_situation,  # ✅ FIX: Campo agregado
                work_condition=member_dto.work_condition,  # ✅ FIX: Campo agregado
                monthly_income=member_dto.monthly_income,  # ✅ FIX: Campo agregado
                disability_type=member_dto.disability_type,
                relationship=member_dto.relationship,
                is_dependent=member_dto.is_dependent
            )
            household_members.append(member)"""
    
    if old_code in content:
        if not dry_run:
            content = content.replace(old_code, new_code)
            
            # Usar el mismo backup si ya existe del fix anterior
            backup_exists = any(file_path.parent.glob(f"{file_path.stem}.py.backup_*"))
            if not backup_exists:
                backup_path = file_path.with_suffix(f'.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                shutil.copy2(file_path, backup_path)
                print_info(f"Backup creado: {backup_path}")
            
            # Escribir archivo corregido
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_success("Campos nuevos agregados en HouseholdMember")
        else:
            print_warning("DRY-RUN: Campos nuevos serían agregados en HouseholdMember")
        return True
    else:
        print_warning("Código no encontrado o ya fue aplicado el fix")
        return False

# ============================================================================
# FIX #3: Actualizar mapeo MongoDB para HouseholdMember
# ============================================================================

def fix_mongodb_household_mapping(dry_run: bool = True) -> bool:
    """Fix #3: Actualizar mapeo MongoDB para HouseholdMember"""
    
    file_path = Path("src/mi_app_completa_backend/infrastructure/persistence/techo_propio/mongo_techo_propio_repository.py")
    
    if not file_path.exists():
        print_error(f"Archivo no encontrado: {file_path}")
        return False
    
    print_info(f"Procesando FIX #3: Mapeo MongoDB de HouseholdMember")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Este fix requiere encontrar los métodos _household_member_to_dict y _dict_to_household_member
    # Por ahora, solo verificamos si existen
    
    if "_household_member_to_dict" in content:
        print_info("Método _household_member_to_dict encontrado")
        
        # Buscar el método y verificar si tiene los campos nuevos
        if "civil_status" in content and "occupation" in content and "employment_situation" in content:
            print_success("Los campos nuevos ya están presentes en el mapeo")
            return True
        else:
            print_warning("Los campos nuevos no están en el mapeo")
            print_info("Este fix requiere intervención manual debido a la complejidad del código")
            print_info("Revisar DIAGNOSTICO_TECHO_PROPIO.md para detalles")
            return False
    else:
        print_error("Método _household_member_to_dict no encontrado")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Script de corrección automática para el módulo Techo Propio"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ver cambios sin aplicarlos"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplicar cambios"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print_error("Debe especificar --dry-run o --apply")
        parser.print_help()
        sys.exit(1)
    
    dry_run = args.dry_run
    
    print_header("SCRIPT DE CORRECCIÓN - MÓDULO TECHO PROPIO")
    
    if dry_run:
        print_warning("MODO DRY-RUN: No se aplicarán cambios")
    else:
        print_info("MODO APLICAR: Se aplicarán los cambios")
        response = input("\n¿Está seguro de continuar? (s/N): ")
        if response.lower() != 's':
            print_info("Operación cancelada")
            sys.exit(0)
    
    print()
    
    # Ejecutar fixes
    results = {}
    
    print_header("FIX #1: Campo address en PropertyInfo")
    results['fix_1'] = fix_property_address(dry_run)
    
    print_header("FIX #2: Campos nuevos en HouseholdMember")
    results['fix_2'] = fix_household_member_fields(dry_run)
    
    print_header("FIX #3: Mapeo MongoDB de HouseholdMember")
    results['fix_3'] = fix_mongodb_household_mapping(dry_run)
    
    # Resumen
    print_header("RESUMEN")
    
    total = len(results)
    successful = sum(1 for v in results.values() if v)
    
    print(f"Total de fixes: {total}")
    print(f"Exitosos: {successful}")
    print(f"Fallidos: {total - successful}")
    print()
    
    for fix_name, success in results.items():
        status = "✅ OK" if success else "❌ FALLO"
        print(f"{fix_name}: {status}")
    
    print()
    
    if dry_run:
        print_warning("DRY-RUN completado. Ejecute con --apply para aplicar cambios.")
    else:
        if successful == total:
            print_success("¡Todos los fixes aplicados exitosamente!")
        else:
            print_warning("Algunos fixes requieren intervención manual.")
            print_info("Revisar DIAGNOSTICO_TECHO_PROPIO.md para más detalles")
    
    print()
    print_header("SIGUIENTE PASO")
    print_info("1. Revisar los cambios aplicados")
    print_info("2. Ejecutar tests: pytest tests/unit/test_techo_propio/")
    print_info("3. Verificar endpoints: POST /api/techo-propio/applications")
    print()

if __name__ == "__main__":
    main()
