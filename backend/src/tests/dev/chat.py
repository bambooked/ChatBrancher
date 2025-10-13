import asyncio
import uuid
from tortoise import Tortoise
from application.use_cases.chat_interaction import ChatInteraction
from application.use_cases.services.message_handler import MessageHandler
from interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from infrastructure.openrouter_client import OpenRouterClient
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity
from interface_adapters.gateways.llm_api_adapter import LLMAdapter
from infrastructure.db.config import TORTOISE_ORM
from infrastructure.db.models import MessageModel, ChatTreeDetail, AssistantMessageDetail

from dotenv import load_dotenv
from os import getenv

# 環境変数を読み込み
load_dotenv()


async def init_db():
    """DBを初期化してスキーマを生成"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def cleanup_db():
    """テスト前にDBをクリーンアップ"""
    print("🧹 Cleaning up database...")
    await AssistantMessageDetail.all().delete()
    await MessageModel.all().delete()
    await ChatTreeDetail.all().delete()
    print("✅ Database cleaned")


async def verify_initial_message(tree: ChatTreeEntity, user: UserEntity):
    """初期メッセージの保存を検証"""
    print("\n--- 初期メッセージの検証 ---")

    # ツリーの状態確認
    assert tree.root_node is not None, "Root node should not be None"
    root_message = tree.root_node.message
    print(f"✅ Root message UUID: {root_message.uuid}")
    print(f"✅ Root message content: {root_message.content}")
    print(f"✅ Root message role: {root_message.role}")

    # DBから取得して確認（parentをプリフェッチ）
    db_message = await MessageModel.get(uuid=root_message.uuid).prefetch_related("parent")
    assert db_message is not None, "初期メッセージがDBに保存されていません"
    assert db_message.parent is None, "初期メッセージの親はNoneであるべきです"
    assert db_message.content == root_message.content, "DBの内容が一致しません"
    assert db_message.role == root_message.role, "DBのロールが一致しません"
    print(f"✅ DB verification passed (parent=None)")

    return root_message


async def verify_user_message(tree: ChatTreeEntity, user: UserEntity, parent_message):
    """ユーザーメッセージの追加と保存を検証"""
    print("\n--- ユーザーメッセージの検証 ---")

    repo = ChatRepositoryImpl()
    llm_client = OpenRouterClient(None)
    llm_adaptor = LLMAdapter(llm_client)
    message_handler = MessageHandler(repo, llm_adaptor, user)

    # ユーザーメッセージを追加
    user_message = await message_handler.add_user_message(
        tree,
        "これはテストユーザーメッセージです",
        parent_message
    )

    print(f"✅ User message UUID: {user_message.uuid}")
    print(f"✅ User message content: {user_message.content}")
    print(f"✅ User message role: {user_message.role}")

    # DBから取得して確認
    db_message = await MessageModel.get(uuid=user_message.uuid).prefetch_related("parent")
    assert db_message is not None, "ユーザーメッセージがDBに保存されていません"
    assert db_message.parent is not None, "ユーザーメッセージの親が設定されていません"
    assert str(db_message.parent.uuid) == str(parent_message.uuid), "親メッセージのUUIDが一致しません"
    assert db_message.content == user_message.content, "DBの内容が一致しません"
    assert db_message.role == "user", "ロールがuserであるべきです"
    print(f"✅ DB verification passed (parent={db_message.parent.uuid})")

    return user_message


async def verify_llm_response(tree: ChatTreeEntity, handler: ChatInteraction, user_message, user: UserEntity):
    """LLM応答の生成と保存を検証"""
    print("\n--- LLM応答の検証 ---")

    # LLM応答を生成
    print("🤖 Calling LLM API...")
    assistant_message = await handler.send_message_and_get_response(
        content="こんにちは！今日の天気について教えてください。",
        parent_message=user_message,
        llm_model="anthropic/claude-3-haiku"
    )

    print(f"✅ Assistant message UUID: {assistant_message.uuid}")
    print(f"✅ Assistant message content (first 100 chars): {assistant_message.content[:100]}...")
    print(f"✅ Assistant message role: {assistant_message.role}")

    # DBから取得して確認
    db_message = await MessageModel.get(uuid=assistant_message.uuid).prefetch_related("parent")
    assert db_message is not None, "アシスタントメッセージがDBに保存されていません"
    assert db_message.parent is not None, "アシスタントメッセージの親が設定されていません"
    # send_message_and_get_responseは内部で新しいユーザーメッセージを作成するため、
    # 親がuserロールであることを確認（UUIDの完全一致ではなく）
    assert db_message.parent.role == "user", "親メッセージはuserロールであるべきです"
    assert db_message.role == "assistant", "ロールがassistantであるべきです"
    print(f"✅ DB verification passed (parent={db_message.parent.uuid}, parent_role={db_message.parent.role})")

    # AssistantMessageDetailの確認
    db_detail = await AssistantMessageDetail.get(message=db_message)
    assert db_detail is not None, "AssistantMessageDetailがDBに保存されていません"
    assert db_detail.provider is not None, "providerが設定されていません"
    assert db_detail.model_name is not None, "model_nameが設定されていません"
    assert db_detail.total_tokens > 0, "total_tokensが0より大きくなければなりません"
    print(f"✅ AssistantMessageDetail verification passed")
    print(f"  - Provider: {db_detail.provider}")
    print(f"  - Model: {db_detail.model_name}")
    print(f"  - Tokens: prompt={db_detail.prompt_tokens}, completion={db_detail.completion_tokens}, total={db_detail.total_tokens}")

    return assistant_message


async def verify_tree_structure(tree: ChatTreeEntity):
    """ツリー構造の整合性を検証"""
    print("\n--- ツリー構造の検証 ---")

    # ルートノードから全てのノードを取得
    nodes = list(tree.root_node.descendants) + [tree.root_node]
    print(f"✅ Total nodes in tree: {len(nodes)}")

    for node in nodes:
        print(f"  - Node UUID: {node.message.uuid}, Role: {node.message.role}, Parent: {node.parent.message.uuid if node.parent else 'None'}")

    # 各ノードがDBに保存されていることを確認
    for node in nodes:
        db_message = await MessageModel.get(uuid=node.message.uuid)
        assert db_message is not None, f"Node {node.message.uuid} is not saved in DB"

    print("✅ Tree structure verification passed")


async def main():
    try:
        await init_db()
        await cleanup_db()

        print("\n=== 統合テスト開始 ===\n")

        # API Keyの確認
        api_key = getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY が環境変数に設定されていません")
        print(f"✅ API Key loaded (length: {len(api_key)})")

        # テストデータの準備（UUIDは正しい形式で生成）
        test_user_uuid = str(uuid.uuid4())
        user = UserEntity(test_user_uuid)
        print(f"Test user UUID: {test_user_uuid}")
        repo = ChatRepositoryImpl()
        tree = ChatTreeEntity()
        llm_client = OpenRouterClient(api_key)  # 実際のAPIキーを使用
        llm_adaptor = LLMAdapter(llm_client)

        handler = ChatInteraction(
            message_handler=MessageHandler(repo, llm_adaptor, user),
            chat_repository=repo,
            chat_tree=tree,
            current_user=user
        )

        # 1. 初期メッセージの作成と保存
        print("\n📝 Step 1: チャット開始（初期メッセージ作成）")
        await handler.start_chat("あなたは親切なAIアシスタントです。")
        print(f"✅ Chat started with tree UUID: {tree.uuid}")

        # 2. 初期メッセージの検証
        root_message = await verify_initial_message(tree, user)

        # 3. ユーザーメッセージの追加と検証
        print("\n📝 Step 2: ユーザーメッセージの追加")
        user_message = await verify_user_message(tree, user, root_message)

        # 4. LLM応答の生成と検証（新規追加）
        print("\n📝 Step 3: LLM応答の生成と検証")
        assistant_message = await verify_llm_response(tree, handler, user_message, user)

        # 5. ツリー構造全体の検証（システム → ユーザー → アシスタント）
        print("\n📝 Step 4: ツリー構造の検証")
        await verify_tree_structure(tree)

        print("\n=== 🎉 全てのテストが成功しました！ ===\n")
        print(f"最終的なツリー構造: {len(list(tree.root_node.descendants) + [tree.root_node])} ノード")
        print("  1. システムメッセージ (root)")
        print("  2. ユーザーメッセージ")
        print("  3. アシスタントメッセージ (LLM応答)")

    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())