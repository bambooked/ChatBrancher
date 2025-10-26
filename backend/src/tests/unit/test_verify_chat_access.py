"""VerifyChatAccessユースケースのユニットテスト"""
import uuid
import pytest
from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.domain.entities.user_entity import UserEntity
from src.domain.entities.message_entity import MessageEntity, Role
from src.application.use_cases.verify_chat_access import VerifyChatAccess, AccessDeniedError


class TestVerifyChatAccess:
    """VerifyChatAccessユースケースのテスト"""

    def test_verify_success_when_user_is_owner(self):
        """ユーザーがチャットの所有者の場合、アクセスが許可される"""
        # Arrange
        owner_uuid = "user-123"
        user = UserEntity(
            uuid=owner_uuid,
            username="testuser",
            email="test@example.com"
        )

        chat_tree = ChatTreeEntity()
        initial_message = MessageEntity(
            uuid="msg-1",
            role=Role.SYSTEM,
            content="Hello"
        )
        chat_tree.new_chat(
            initial_message,
            owner_uuid=owner_uuid,
            chat_uuid=uuid.uuid4(),
        )

        use_case = VerifyChatAccess()

        # Act & Assert
        # 所有者なので例外が発生しない
        use_case.verify(user, chat_tree)

    def test_verify_raises_error_when_user_is_not_owner(self):
        """ユーザーがチャットの所有者でない場合、AccessDeniedErrorが発生"""
        # Arrange
        owner_uuid = "user-123"
        other_user_uuid = "user-456"

        other_user = UserEntity(
            uuid=other_user_uuid,
            username="otheruser",
            email="other@example.com"
        )

        chat_tree = ChatTreeEntity()
        initial_message = MessageEntity(
            uuid="msg-1",
            role=Role.SYSTEM,
            content="Hello"
        )
        chat_tree.new_chat(
            initial_message,
            owner_uuid=owner_uuid,
            chat_uuid=uuid.uuid4(),
        )

        use_case = VerifyChatAccess()

        # Act & Assert
        with pytest.raises(AccessDeniedError) as exc_info:
            use_case.verify(other_user, chat_tree)

        assert "access denied" in str(exc_info.value).lower()

    def test_verify_raises_error_when_user_is_inactive(self):
        """ユーザーが無効化されている場合、AccessDeniedErrorが発生"""
        # Arrange
        owner_uuid = "user-123"
        inactive_user = UserEntity(
            uuid=owner_uuid,
            username="inactiveuser",
            email="inactive@example.com",
            is_active=False
        )

        chat_tree = ChatTreeEntity()
        initial_message = MessageEntity(
            uuid="msg-1",
            role=Role.SYSTEM,
            content="Hello"
        )
        chat_tree.new_chat(
            initial_message,
            owner_uuid=owner_uuid,
            chat_uuid=uuid.uuid4(),
        )

        use_case = VerifyChatAccess()

        # Act & Assert
        with pytest.raises(AccessDeniedError) as exc_info:
            use_case.verify(inactive_user, chat_tree)

        assert "inactive" in str(exc_info.value).lower()
