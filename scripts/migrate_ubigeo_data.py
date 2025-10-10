#!/usr/bin/env python3
"""
Script de migración para cargar datos UBIGEO desde CSV a MongoDB
Carga departamentos, provincias y distritos del Perú
"""

import csv
import os
import sys
from typing import Dict, List
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UbigeoMigrator:
    def __init__(self, mongodb_url: str = "mongodb://localhost:27017", db_name: str = "mi_app_completa_db"):
        self.client = MongoClient(mongodb_url)
        self.db = self.client[db_name]
        self.collection = self.db.ubigeo_locations
        
        # Crear índices para optimizar consultas
        self.setup_indexes()
    
    def setup_indexes(self):
        """Crear índices para optimizar consultas"""
        try:
            # Índice único por código UBIGEO
            self.collection.create_index("ubigeo_code", unique=True)
            
            # Índices para consultas frecuentes
            self.collection.create_index("department")
            self.collection.create_index([("department", 1), ("province", 1)])
            self.collection.create_index([("department", 1), ("province", 1), ("district", 1)])
            
            logger.info("✅ Índices creados correctamente")
        except Exception as e:
            logger.warning(f"⚠️ Error creando índices: {e}")
    
    def generate_ubigeo_code(self, dept_code: str, prov_code: str, dist_code: str) -> str:
        """Generar código UBIGEO de 6 dígitos"""
        return f"{dept_code.zfill(2)}{prov_code.zfill(2)}{dist_code.zfill(2)}"
    
    def get_department_code(self, department: str) -> str:
        """Mapear nombres de departamentos a códigos oficiales"""
        dept_codes = {
            'AMAZONAS': '01', 'ANCASH': '02', 'APURIMAC': '03', 'AREQUIPA': '04',
            'AYACUCHO': '05', 'CAJAMARCA': '06', 'CALLAO': '07', 'CUSCO': '08',
            'HUANCAVELICA': '09', 'HUANUCO': '10', 'ICA': '11', 'JUNIN': '12',
            'LA LIBERTAD': '13', 'LAMBAYEQUE': '14', 'LIMA': '15', 'LORETO': '16',
            'MADRE DE DIOS': '17', 'MOQUEGUA': '18', 'PASCO': '19', 'PIURA': '20',
            'PUNO': '21', 'SAN MARTIN': '22', 'TACNA': '23', 'TUMBES': '24',
            'UCAYALI': '25'
        }
        return dept_codes.get(department.upper().strip(), '99')
    
    def clear_collection(self):
        """Limpiar la colección antes de la migración"""
        count = self.collection.count_documents({})
        if count > 0:
            result = self.collection.delete_many({})
            logger.info(f"🗑️ Eliminados {result.deleted_count} documentos existentes")
    
    def load_csv_data(self, csv_file_path: str) -> List[Dict]:
        """Cargar y procesar datos del CSV"""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"Archivo CSV no encontrado: {csv_file_path}")
        
        data = []
        department_counters = {}  # Para generar códigos de provincia/distrito
        province_counters = {}
        
        logger.info(f"📖 Leyendo archivo CSV: {csv_file_path}")
        
        try:
            # Intentar diferentes encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(csv_file_path, 'r', encoding=encoding) as file:
                        csv_reader = csv.reader(file, delimiter=';')  # Usar ; como delimitador
                        next(csv_reader)  # Saltar header

                        for row in csv_reader:
                            if len(row) >= 4:
                                district = row[1].strip().upper()
                                province = row[2].strip().upper()
                                department = row[3].strip().upper()
                                
                                # Generar códigos
                                dept_code = self.get_department_code(department)
                                
                                # Código de provincia
                                dept_prov_key = f"{department}_{province}"
                                if dept_prov_key not in province_counters:
                                    if department not in department_counters:
                                        department_counters[department] = 0
                                    department_counters[department] += 1
                                    province_counters[dept_prov_key] = department_counters[department]
                                prov_code = str(province_counters[dept_prov_key]).zfill(2)
                                
                                # Código de distrito
                                prov_dist_key = f"{department}_{province}_{district}"
                                if prov_dist_key not in province_counters:
                                    if dept_prov_key not in department_counters:
                                        department_counters[dept_prov_key] = 0
                                    department_counters[dept_prov_key] += 1
                                    province_counters[prov_dist_key] = department_counters[dept_prov_key]
                                dist_code = str(province_counters[prov_dist_key]).zfill(2)
                                
                                ubigeo_code = self.generate_ubigeo_code(dept_code, prov_code, dist_code)
                                
                                data.append({
                                    'ubigeo_code': ubigeo_code,
                                    'department': department,
                                    'province': province,
                                    'district': district,
                                    'department_code': dept_code,
                                    'province_code': prov_code,
                                    'district_code': dist_code
                                })
                    
                    logger.info(f"✅ CSV leído con encoding {encoding}")
                    break
                    
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("No se pudo leer el archivo CSV con ningún encoding")
                
        except Exception as e:
            logger.error(f"❌ Error leyendo CSV: {e}")
            raise
        
        logger.info(f"📊 Procesados {len(data)} registros del CSV")
        return data
    
    def insert_data(self, data: List[Dict]):
        """Insertar datos en MongoDB"""
        logger.info("💾 Insertando datos en MongoDB...")
        
        try:
            # Insertar en lotes para mejor performance
            batch_size = 1000
            inserted_count = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                try:
                    result = self.collection.insert_many(batch, ordered=False)
                    inserted_count += len(result.inserted_ids)
                    logger.info(f"📦 Lote insertado: {len(result.inserted_ids)} documentos")
                except Exception as e:
                    logger.warning(f"⚠️ Error en lote: {e}")
            
            logger.info(f"✅ Migración completada: {inserted_count} documentos insertados")
            
        except Exception as e:
            logger.error(f"❌ Error insertando datos: {e}")
            raise
    
    def verify_data(self):
        """Verificar que los datos se insertaron correctamente"""
        total_count = self.collection.count_documents({})
        dept_count = len(self.collection.distinct("department"))
        prov_count = len(self.collection.distinct("province"))
        
        logger.info(f"🔍 Verificación:")
        logger.info(f"  - Total distritos: {total_count}")
        logger.info(f"  - Departamentos: {dept_count}")
        logger.info(f"  - Provincias: {prov_count}")
        
        # Mostrar algunos ejemplos
        sample = list(self.collection.find().limit(5))
        logger.info("📋 Ejemplos de datos:")
        for doc in sample:
            logger.info(f"  - {doc['ubigeo_code']}: {doc['department']} > {doc['province']} > {doc['district']}")
    
    def migrate(self, csv_file_path: str, clear_existing: bool = True):
        """Ejecutar migración completa"""
        logger.info("🚀 Iniciando migración de datos UBIGEO")
        
        try:
            if clear_existing:
                self.clear_collection()
            
            data = self.load_csv_data(csv_file_path)
            self.insert_data(data)
            self.verify_data()
            
            logger.info("🎉 Migración completada exitosamente")
            
        except Exception as e:
            logger.error(f"💥 Error en migración: {e}")
            raise
        finally:
            self.client.close()

def main():
    # Configuración
    csv_file = "c:\\Users\\pc1\\Desktop\\AppTc\\departamentos_provincias_distritos_perucsv.csv"
    mongodb_url = "mongodb://localhost:27017"
    db_name = "apptc"  # Base de datos correcta

    print(f"[INFO] Iniciando migracion de UBIGEO")
    print(f"[INFO] CSV: {csv_file}")
    print(f"[INFO] Database: {db_name}")

    # Ejecutar migración
    migrator = UbigeoMigrator(mongodb_url, db_name)
    migrator.migrate(csv_file, clear_existing=True)

if __name__ == "__main__":
    main()