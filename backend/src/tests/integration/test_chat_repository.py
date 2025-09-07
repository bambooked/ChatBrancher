import pytest
import pytest_asyncio
import os
import tempfile
import uuid
from tortoise import Tortoise

from src.domain.entities.message_entity import MessageEntity, Role
from src.interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from src.infrastructure.models import MessageModel, AssistantMessageDetail


class TestChatRepositoryIntegration:
    """チャットリポジトリの統合テスト（TDD）"""
    
    @pytest_asyncio.fixture
    async def setup_db(self):
        """テスト用SQLiteデータベースのセットアップ"""
        # テンポラリファイルでSQLiteを使用
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        await Tortoise.init(
            db_url=f'sqlite://{db_path}',
            modules={'models': ['src.infrastructure.models']}
        )
        await Tortoise.generate_schemas()
        
        yield db_path
        
        # クリーンアップ
        await Tortoise.close_connections()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_database_connection_and_schema_creation(self, setup_db):
        """テスト1: データベース接続とスキーマ作成ができる"""
        db_path = setup_db
        # データベースが正しく初期化されていることを確認
        assert os.path.exists(db_path)
        
        # テーブルが作成されていることを確認
        message_count = await MessageModel.all().count()
        assert message_count == 0  # 初期状態では0件
        
        detail_count = await AssistantMessageDetail.all().count()
        assert detail_count == 0  # 初期状態では0件
    
    @pytest.mark.asyncio
    async def test_save_user_message(self, setup_db):
        """テスト2: ユーザーメッセージを保存できる"""
        repo = ChatRepositoryImpl()
        
        # テストデータの準備
        message_uuid = str(uuid.uuid4())
        chat_tree_id = str(uuid.uuid4())
        user_context_id = str(uuid.uuid4())
        
        message_entity = MessageEntity(
            uuid=message_uuid,
            role=Role.USER,
            content="Hello, this is a test message"
        )
        
        # メッセージを保存
        await repo.save_message(
            message_entity=message_entity,
            chat_tree_id=chat_tree_id,
            parent_uuid=None,  # ルートメッセージ
            user_context_id=user_context_id
        )
        
        # データベースから取得して検証
        saved_message = await MessageModel.get(uuid=message_uuid)
        assert str(saved_message.uuid) == message_uuid
        assert saved_message.role == Role.USER
        assert saved_message.content == "Hello, this is a test message"
        assert str(saved_message.chat_tree_id) == chat_tree_id
        assert saved_message.parent_uuid is None
        assert str(saved_message.user_context_id) == user_context_id
    
    @pytest.mark.asyncio
    async def test_save_assistant_message_with_parent(self, setup_db):
        """テスト3: 親を持つアシスタントメッセージを保存できる"""
        repo = ChatRepositoryImpl()
        
        # まず親メッセージを保存
        parent_uuid = str(uuid.uuid4())
        chat_tree_id = str(uuid.uuid4())
        
        parent_message = MessageEntity(
            uuid=parent_uuid,
            role=Role.USER,
            content="Parent message"
        )
        
        await repo.save_message(
            message_entity=parent_message,
            chat_tree_id=chat_tree_id,
            parent_uuid=None
        )
        
        # 子メッセージを保存
        child_uuid = str(uuid.uuid4())
        child_message = MessageEntity(
            uuid=child_uuid,
            role=Role.ASSISTANT,
            content="Child response message"
        )
        
        await repo.save_message(
            message_entity=child_message,
            chat_tree_id=chat_tree_id,
            parent_uuid=parent_uuid
        )
        
        # データベースから取得して検証
        saved_child = await MessageModel.get(uuid=child_uuid)
        assert str(saved_child.uuid) == child_uuid
        assert saved_child.role == Role.ASSISTANT
        assert saved_child.content == "Child response message"
        assert str(saved_child.parent_uuid) == parent_uuid
        assert str(saved_child.chat_tree_id) == chat_tree_id

    @pytest.mark.asyncio
    async def test_get_chat_tree_messages(self, setup_db):
        """テスト6: チャット木に属する全メッセージを一括取得できる"""
        repo = ChatRepositoryImpl()
        
        # 共通のチャット木ID
        chat_tree_id = str(uuid.uuid4())
        
        # 複数のメッセージを異なる親子関係で保存
        root_uuid = str(uuid.uuid4())
        child1_uuid = str(uuid.uuid4())
        child2_uuid = str(uuid.uuid4())
        grandchild_uuid = str(uuid.uuid4())
        
        # ルートメッセージ
        root_message = MessageEntity(
            uuid=root_uuid,
            role=Role.SYSTEM,
            content="System prompt"
        )
        await repo.save_message(root_message, chat_tree_id, None)
        
        # 子メッセージ1（ユーザー）
        child1_message = MessageEntity(
            uuid=child1_uuid,
            role=Role.USER,
            content="User question 1"
        )
        await repo.save_message(child1_message, chat_tree_id, root_uuid)
        
        # 子メッセージ2（アシスタント）
        child2_message = MessageEntity(
            uuid=child2_uuid,
            role=Role.ASSISTANT,
            content="Assistant response 1"
        )
        await repo.save_message(child2_message, chat_tree_id, child1_uuid)
        
        # 孫メッセージ（ユーザー）
        grandchild_message = MessageEntity(
            uuid=grandchild_uuid,
            role=Role.USER,
            content="Follow-up question"
        )
        await repo.save_message(grandchild_message, chat_tree_id, child2_uuid)
        
        # 別のチャット木にも1つメッセージを保存（除外されることを確認）
        other_chat_tree_id = str(uuid.uuid4())
        other_message_uuid = str(uuid.uuid4())
        other_message = MessageEntity(
            uuid=other_message_uuid,
            role=Role.USER,
            content="Different chat tree message"
        )
        await repo.save_message(other_message, other_chat_tree_id, None)
        
        # 対象チャット木のメッセージを一括取得
        messages = await repo.get_chat_tree_messages(chat_tree_id)
        
        # 検証
        assert len(messages) == 4  # 対象チャット木のメッセージのみ
        
        # UUIDリストを取得して確認
        retrieved_uuids = [msg['uuid'] for msg in messages]
        expected_uuids = [root_uuid, child1_uuid, child2_uuid, grandchild_uuid]
        
        for expected_uuid in expected_uuids:
            assert expected_uuid in retrieved_uuids
        
        # 他のチャット木のメッセージが含まれていないことを確認
        assert other_message_uuid not in retrieved_uuids
        
        # 作成順でソートされていることを確認（created_atで）
        assert messages[0]['uuid'] == root_uuid  # 最初に作成
        assert messages[0]['content'] == "System prompt"
        assert messages[0]['parent_uuid'] is None  # ルートメッセージ
        assert messages[1]['uuid'] == child1_uuid
        assert messages[1]['parent_uuid'] == root_uuid
        assert messages[2]['uuid'] == child2_uuid
        assert messages[2]['parent_uuid'] == child1_uuid
        assert messages[3]['uuid'] == grandchild_uuid  # 最後に作成
        assert messages[3]['parent_uuid'] == child2_uuid
        
        # 空のチャット木IDでの取得
        empty_chat_tree_id = str(uuid.uuid4())
        empty_messages = await repo.get_chat_tree_messages(empty_chat_tree_id)
        assert len(empty_messages) == 0
    
    @pytest.mark.asyncio
    async def test_restore_chat_tree_from_message_list(self, setup_db):
        """テスト7: メッセージリストからChatTreeEntityを復元できる"""
        from src.domain.entities.chat_tree_entity import ChatTreeEntity
        from src.domain.entities.message_entity import MessageEntity, Role
        
        repo = ChatRepositoryImpl()
        
        # テストデータを保存（複雑な木構造）
        chat_tree_id = str(uuid.uuid4())
        
        # ルート（システムプロンプト）
        root_uuid = str(uuid.uuid4())
        root_message = MessageEntity(
            uuid=root_uuid,
            role=Role.SYSTEM,
            content="You are a helpful assistant"
        )
        await repo.save_message(root_message, chat_tree_id, None)
        
        # 第1レベル：ユーザー質問
        user1_uuid = str(uuid.uuid4())
        user1_message = MessageEntity(
            uuid=user1_uuid,
            role=Role.USER,
            content="What is Python?"
        )
        await repo.save_message(user1_message, chat_tree_id, root_uuid)
        
        # 第2レベル：アシスタント回答
        assistant1_uuid = str(uuid.uuid4())
        assistant1_message = MessageEntity(
            uuid=assistant1_uuid,
            role=Role.ASSISTANT,
            content="Python is a programming language"
        )
        await repo.save_message(assistant1_message, chat_tree_id, user1_uuid)
        
        # 第3レベル：ユーザー追加質問（分岐1）
        user2_uuid = str(uuid.uuid4())
        user2_message = MessageEntity(
            uuid=user2_uuid,
            role=Role.USER,
            content="Can you give me an example?"
        )
        await repo.save_message(user2_message, chat_tree_id, assistant1_uuid)
        
        # 第3レベル：ユーザー追加質問（分岐2）
        user3_uuid = str(uuid.uuid4())
        user3_message = MessageEntity(
            uuid=user3_uuid,
            role=Role.USER,
            content="What are its benefits?"
        )
        await repo.save_message(user3_message, chat_tree_id, assistant1_uuid)
        
        # リポジトリからメッセージリストを取得
        message_list = await repo.get_chat_tree_messages(chat_tree_id)
        
        # ChatTreeEntityに復元
        restored_tree = ChatTreeEntity.restore_from_message_list(message_list)
        
        # 復元されたツリーの検証
        assert restored_tree.root_node is not None
        assert restored_tree.root_node.message.uuid == root_uuid
        assert restored_tree.root_node.message.content == "You are a helpful assistant"
        
        # 子ノード（ユーザー質問）の確認
        assert len(restored_tree.root_node.children) == 1
        user1_node = restored_tree.root_node.children[0]
        assert user1_node.message.uuid == user1_uuid
        assert user1_node.message.content == "What is Python?"
        
        # 孫ノード（アシスタント回答）の確認
        assert len(user1_node.children) == 1
        assistant1_node = user1_node.children[0]
        assert assistant1_node.message.uuid == assistant1_uuid
        assert assistant1_node.message.content == "Python is a programming language"
        
        # ひ孫ノード（分岐した質問）の確認
        assert len(assistant1_node.children) == 2
        branch_uuids = [child.message.uuid for child in assistant1_node.children]
        assert user2_uuid in branch_uuids
        assert user3_uuid in branch_uuids
        
        # 会話パスの取得テスト
        user2_entity = MessageEntity(uuid=user2_uuid, role=Role.USER, content="Can you give me an example?")
        conversation_path = restored_tree.get_conversation_path(user2_entity)
        
        # パスの順序確認（ルート → user1 → assistant1 → user2）
        assert len(conversation_path) == 4
        assert conversation_path[0].uuid == root_uuid
        assert conversation_path[1].uuid == user1_uuid
        assert conversation_path[2].uuid == assistant1_uuid
        assert conversation_path[3].uuid == user2_uuid