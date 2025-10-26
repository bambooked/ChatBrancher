"""ChatTreeEntityのユニットテスト"""
import pytest
import uuid
from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.domain.entities.message_entity import MessageEntity, Role


class TestChatTreeEntityOwnership:
    """ChatTreeEntityの所有権管理機能テスト"""

    def test_new_chat_with_owner(self):
        """owner_uuidを指定して新しいチャットを作成できる"""
        # Arrange
        tree = ChatTreeEntity()
        owner_uuid = "user-123"
        initial_message = MessageEntity(
            uuid=str(uuid.uuid4()),
            role=Role.SYSTEM,
            content="Hello"
        )
        chat_uuid = uuid.uuid4()

        # Act
        tree.new_chat(
            initial_message,
            owner_uuid=owner_uuid,
            chat_uuid=chat_uuid,
        )

        # Assert
        assert tree.owner_uuid == owner_uuid
        assert tree.uuid == chat_uuid
        assert tree.root_node is not None

    def test_new_chat_without_owner_raises_error(self):
        """owner_uuidを指定せずに新しいチャットを作成しようとするとエラー"""
        # Arrange
        tree = ChatTreeEntity()
        initial_message = MessageEntity(
            uuid=str(uuid.uuid4()),
            role=Role.SYSTEM,
            content="Hello"
        )
        chat_uuid = uuid.uuid4()

        # Act & Assert
        with pytest.raises(TypeError):
            tree.new_chat(initial_message, chat_uuid=chat_uuid)

    def test_revert_chat_with_owner(self):
        """owner_uuidを含めてチャットを復元できる"""
        # Arrange
        tree = ChatTreeEntity()
        chat_uuid = str(uuid.uuid4())
        owner_uuid = "user-456"
        messages = [
            {
                "uuid": str(uuid.uuid4()),
                "role": "system",
                "content": "System message",
                "parent_uuid": None
            }
        ]

        # Act
        tree.revert_chat(chat_uuid, messages, owner_uuid=owner_uuid)

        # Assert
        assert tree.owner_uuid == owner_uuid
        assert str(tree.uuid) == chat_uuid

    def test_is_owned_by(self):
        """指定されたユーザーがチャットの所有者かどうかを判定できる"""
        # Arrange
        tree = ChatTreeEntity()
        owner_uuid = "user-789"
        initial_message = MessageEntity(
            uuid=str(uuid.uuid4()),
            role=Role.SYSTEM,
            content="Hello"
        )
        tree.new_chat(
            initial_message,
            owner_uuid=owner_uuid,
            chat_uuid=uuid.uuid4(),
        )

        # Act & Assert
        assert tree.is_owned_by(owner_uuid) is True
        assert tree.is_owned_by("other-user") is False
