import pytest
from src.mi_app_completa_backend.domain.entities.user import User

class TestUserEntity:
    """Tests para la entidad User"""

    def test_create_user(self):
        """Test crear usuario"""
        user = User(name="Juan Pérez", email="juan@example.com")

        assert user.name == "Juan Pérez"
        assert user.email == "juan@example.com"
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_change_name(self):
        """Test cambiar nombre de usuario"""
        user = User(name="Juan Pérez", email="juan@example.com")
        original_updated_at = user.updated_at

        user.change_name("Juan Carlos Pérez")

        assert user.name == "Juan Carlos Pérez"
        assert user.updated_at > original_updated_at

    def test_change_name_empty_raises_error(self):
        """Test cambiar nombre vacío genera error"""
        user = User(name="Juan Pérez", email="juan@example.com")

        with pytest.raises(ValueError, match="El nombre no puede estar vacío"):
            user.change_name("")

    def test_change_email(self):
        """Test cambiar email de usuario"""
        user = User(name="Juan Pérez", email="juan@example.com")
        original_updated_at = user.updated_at

        user.change_email("JUAN.CARLOS@EXAMPLE.COM")

        assert user.email == "juan.carlos@example.com"
        assert user.updated_at > original_updated_at

    def test_change_invalid_email_raises_error(self):
        """Test cambiar email inválido genera error"""
        user = User(name="Juan Pérez", email="juan@example.com")

        with pytest.raises(ValueError, match="Email inválido"):
            user.change_email("email_invalido")

    def test_user_equality(self):
        """Test igualdad entre usuarios"""
        user1 = User(name="Juan", email="juan@example.com", id="123")
        user2 = User(name="Pedro", email="pedro@example.com", id="123")
        user3 = User(name="Juan", email="juan@example.com", id="456")

        assert user1 == user2  # Mismo ID
        assert user1 != user3  # Diferente ID