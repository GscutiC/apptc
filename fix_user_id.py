"""Script para agregar user_id a documentos existentes"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['apptc']
collection = db['techo_propio_applications']

# ID de usuario real obtenido de la base de datos
TEST_USER_ID = "user_339MX93RuwYOONURelR2HCxBrDU"  # ✅ Clerk ID real

print(f'📋 Buscando documentos sin user_id...')
docs_sin_user_id = collection.count_documents({"user_id": None})
print(f'📊 Documentos encontrados: {docs_sin_user_id}')

if docs_sin_user_id > 0:
    print(f'\n✅ Actualizando documentos con user_id: {TEST_USER_ID}')
    result = collection.update_many(
        {"user_id": None},  # Filtro: documentos sin user_id
        {"$set": {"user_id": TEST_USER_ID}}  # Actualización: agregar user_id
    )
    print(f'✅ {result.modified_count} documentos actualizados')
else:
    print('\n✅ Todos los documentos ya tienen user_id')

# Verificar
doc = collection.find_one()
print(f'\n🔍 Verificación - user_id del primer documento: {doc.get("user_id")}')
print(f'🔍 created_by: {doc.get("created_by")}')
