"""UserEntityのユニットテスト"""
from src.domain.entities.user_entity import UserEntity


class TestUserEntity:
    """UserEntityの基本機能テスト"""

    def test_create_user_with_basic_info(self):
        """username, email, is_activeを持つUserEntityを作成できる"""
        # Arrange & Act
        user = UserEntity(
            uuid="test-uuid-123",
            username="testuser",
            email="test@example.com",
            is_active=True
        )

        # Assert
        assert user.uuid == "test-uuid-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_create_inactive_user(self):
        """is_active=Falseのユーザーを作成できる"""
        # Arrange & Act
        user = UserEntity(
            uuid="test-uuid-456",
            username="inactiveuser",
            email="inactive@example.com",
            is_active=False
        )

        # Assert
        assert user.is_active is False

    def test_user_with_default_active_status(self):
        """is_activeのデフォルト値はTrue"""
        # Arrange & Act
        user = UserEntity(
            uuid="test-uuid-789",
            username="defaultuser",
            email="default@example.com"
        )

        # Assert
        assert user.is_active is True
