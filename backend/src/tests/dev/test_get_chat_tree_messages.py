import asyncio
import uuid
from tortoise import Tortoise
from application.use_cases.chat_interaction import ChatInteraction
from application.use_cases.services.message_handler import MessageHandler
from application.use_cases.chat_selection import ChatSelection
from interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from infrastructure.openrouter_client import OpenRouterClient
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity
from interface_adapters.gateways.llm_api_adapter import LLMAdapter
from infrastructure.db.config import TORTOISE_ORM
from infrastructure.db.models import MessageModel, ChatTreeDetail, AssistantMessageDetail, UserModel

from dotenv import load_dotenv

load_dotenv()


async def init_db():
    """DBを初期化"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def cleanup_db():
    """DBをクリーンアップ"""
    print("🧹 データベースをクリーンアップ中...")
    await AssistantMessageDetail.all().delete()
    await MessageModel.all().delete()
    await ChatTreeDetail.all().delete()
    await UserModel.all().delete()
    print("✅ クリーンアップ完了")


async def test_get_chat_tree_messages():
    """get_chat_tree_messagesメソッドのテスト"""
    try:
        await init_db()
        await cleanup_db()

        print("\n=== get_chat_tree_messages テスト開始 ===\n")

        # テストユーザーの準備
        user_uuid = uuid.uuid4()
        user = UserEntity(
            uuid=str(user_uuid),
            username="test_user",
            email="test@example.com"
        )

        # テストユーザーをDBに作成
        await UserModel.create(
            uuid=user_uuid,
            username=user.username,
            email=user.email,
            password_hash="test_hash",  # テスト用のダミーハッシュ
            is_active=True
        )
        print(f"テストユーザーUUID: {user.uuid}")

        # リポジトリとチャットツリーの準備
        repo = ChatRepositoryImpl()
        tree = ChatTreeEntity()
        llm_client = OpenRouterClient(None)  # テスト用にAPIキー不要
        llm_adaptor = LLMAdapter(llm_client)
        message_handler = MessageHandler(repo, llm_adaptor, user)

        handler = ChatInteraction(
            message_handler=message_handler,
            chat_repository=repo,
            chat_tree=tree,
            current_user=user
        )

        # Step 1: チャットを開始
        print("\n📝 Step 1: チャットを開始")
        await handler.start_chat("あなたは親切なAIアシスタントです。")
        print(f"✅ チャットツリーUUID: {tree.uuid}")
        tree_uuid = str(tree.uuid)

        # Step 2: ユーザーメッセージを追加
        print("\n📝 Step 2: ユーザーメッセージを追加")
        root_message = tree.root_node.message
        user_message = await message_handler.add_user_message(
            tree,
            "こんにちは、これはテストメッセージです。",
            root_message
        )
        print(f"✅ ユーザーメッセージUUID: {user_message.uuid}")

        # Step 3: get_chat_tree_messagesでメッセージを取得
        print("\n📝 Step 3: get_chat_tree_messagesでメッセージを取得")
        messages = await repo.get_chat_tree_messages(tree_uuid, user)

        if messages is None:
            print("❌ メッセージが取得できませんでした")
            return

        print(f"✅ {len(messages)}件のメッセージを取得")
        for msg in messages:
            print(f"  - UUID: {msg['uuid']}, Role: {msg['role']}, Parent: {msg['parent_uuid']}")

        # Step 4: 取得したメッセージからツリーを復元
        print("\n📝 Step 4: メッセージリストからチャットツリーを復元")
        chat_selection = ChatSelection(repo, user)
        restored_tree = await chat_selection.get_chat_tree(tree_uuid)

        print(f"✅ ツリーを復元しました")
        print(f"✅ 復元されたツリーUUID: {restored_tree.uuid}")

        # Step 5: 復元されたツリーの構造を確認
        print("\n📝 Step 5: 復元されたツリーの構造を確認")
        nodes = list(restored_tree.root_node.descendants) + [restored_tree.root_node]
        print(f"✅ 復元されたツリーのノード数: {len(nodes)}")

        for node in nodes:
            parent_uuid = node.parent.message.uuid if node.parent else None
            print(f"  - UUID: {node.message.uuid}, Role: {node.message.role}, Parent: {parent_uuid}")

        # Step 6: 元のツリーと復元されたツリーを比較
        print("\n📝 Step 6: 元のツリーと復元されたツリーを比較")
        original_nodes = list(tree.root_node.descendants) + [tree.root_node]
        restored_nodes = list(restored_tree.root_node.descendants) + [restored_tree.root_node]

        assert len(original_nodes) == len(restored_nodes), "ノード数が一致しません"
        print(f"✅ ノード数が一致: {len(original_nodes)}")

        # UUIDのセットで比較
        original_uuids = {str(node.message.uuid) for node in original_nodes}
        restored_uuids = {str(node.message.uuid) for node in restored_nodes}

        assert original_uuids == restored_uuids, "ノードのUUIDが一致しません"
        print(f"✅ 全てのノードUUIDが一致")

        print("\n=== 🎉 テスト成功！get_chat_tree_messagesは正しく動作しています ===\n")

    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_get_chat_tree_messages())
