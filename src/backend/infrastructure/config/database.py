from pymongo import MongoClient
from pymongo.database import Database
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .settings import settings


class DatabaseConfig:
    """Configuración de la base de datos"""

    def __init__(self):
        self.mongodb_url = settings.mongodb_url
        self.database_name = settings.database_name
        self._client = None
        self._database = None
        self._async_client = None
        self._async_database = None

    def get_database(self) -> Database:
        """Obtener instancia de la base de datos (síncrona)"""
        if self._database is None:
            self._client = MongoClient(self.mongodb_url)
            self._database = self._client[self.database_name]
        return self._database
    
    def get_async_database(self) -> AsyncIOMotorDatabase:
        """Obtener instancia de la base de datos (asíncrona)"""
        if self._async_database is None:
            self._async_client = AsyncIOMotorClient(self.mongodb_url)
            self._async_database = self._async_client[self.database_name]
        return self._async_database

    def close_connection(self):
        """Cerrar conexión a la base de datos"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
        if self._async_client:
            self._async_client.close()
            self._async_client = None
            self._async_database = None

# Instancia global de configuración de base de datos
_db_config = DatabaseConfig()

def get_database() -> AsyncIOMotorDatabase:
    """Función utilitaria para obtener la base de datos asíncrona"""
    return _db_config.get_async_database()