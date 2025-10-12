"""Script temporal para verificar MongoDB"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['apptc']  # ✅ CORRECTO: Base de datos según .env
collection = db['techo_propio_applications']

count = collection.count_documents({})
print(f'📊 Total documentos en apptc.techo_propio_applications: {count}')

if count > 0:
    doc = collection.find_one()
    print(f'\n✅ Documento encontrado')
    print(f'📋 Campos principales: {list(doc.keys())}')
    print(f'\n🔍 user_id: {doc.get("user_id")}')
    print(f'🔍 created_by: {doc.get("created_by")}')
    print(f'🔍 status: {doc.get("status")}')
    print(f'🔍 main_applicant exists: {"main_applicant" in doc}')
    print(f'🔍 head_of_family exists: {"head_of_family" in doc}')
    
    # Mostrar más detalles
    if "main_applicant" in doc:
        print(f'\n👤 main_applicant.document_number: {doc["main_applicant"].get("document_number")}')
        print(f'👤 main_applicant.first_name: {doc["main_applicant"].get("first_name")}')
else:
    print('\n❌ No se encontraron documentos')

