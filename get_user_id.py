"""Obtener clerk_id del usuario"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['apptc']

# Buscar usuario
user = db['users'].find_one()
if user:
    print(f'👤 Usuario encontrado: {user.get("email")}')
    print(f'🔑 Clerk ID: {user.get("clerk_id")}')
    print(f'📧 Email: {user.get("email")}')
else:
    print('❌ No se encontró usuario. Usando ID por defecto.')
    print('🔑 Clerk ID por defecto: user_2pHSLrXMVQYSXRZHODEiNLXjxmb')
