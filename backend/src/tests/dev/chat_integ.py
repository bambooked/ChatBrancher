import asyncio
import uuid
import random
from tortoise import Tortoise

from application.use_cases.chat_interaction import ChatInteraction
from application.use_cases.chat_selection import ChatSelection
from application.use_cases.services.message_handler import MessageHandler
from interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from infrastructure.openrouter_client import OpenRouterClient
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity
from interface_adapters.gateways.llm_api_adapter import LLMAdapter
from infrastructure.db.config import TORTOISE_ORM
#from infrastructure.db.models import MessageModel, ChatTreeDetail, AssistantMessageDetail

from dotenv import load_dotenv
from os import getenv
load_dotenv()

async def start_chat(interaction_handler: ChatInteraction) -> None:
    await interaction_handler.start_chat(
        initial_message="あなたは優秀なアシスタントです。userは日本語の回答を期待しています。"
        )
    #print(interaction_handler.chat_tree.root_node.message.content)

async def continue_chat(
        interaction_handler: ChatInteraction,
        message: str
        ) -> None:
    parent_message = interaction_handler.chat_tree.root_node.message
    resp = await interaction_handler.send_message_and_get_response(
        content=message,
        parent_message_uuid=parent_message.uuid,
        llm_model="anthropic/claude-3-haiku"
    )
    #print(resp)

async def branch_chat(selector: ChatSelection, interaction_handler: ChatInteraction) -> None:
    """ランダムなメッセージから分岐してLLM応答を生成"""
    # interaction_handler.chat_treeから直接メッセージを取得（インスタンスの一貫性を保つ）
    if interaction_handler.chat_tree.root_node is None:
        print("❌ ツリーにメッセージがありません")
        return

    all_nodes = [interaction_handler.chat_tree.root_node] + list(interaction_handler.chat_tree.root_node.descendants)
    all_message_uuids = [str(node.message.uuid) for node in all_nodes]
    all_messages = [node.message for node in all_nodes]

    print(f"ツリー内のメッセージ数: {len(all_message_uuids)}")

    # ランダムにメッセージを選択
    random_message = random.choice(all_messages)

    # 選択されたメッセージから分岐
    branch_response = await interaction_handler.send_message_and_get_response(
        content="短めに自己紹介してみて！",
        parent_message_uuid=random_message.uuid,
        llm_model="anthropic/claude-3-haiku"
    )

    interaction_handler.chat_tree._render_tree()


async def restart_chat(selector: ChatSelection) -> ChatTreeEntity:
    chat_uuids = await selector.get_all_chat_uuid()
    recent_chat_uuid = chat_uuids[-1]
    chat_tree = await selector.restart_chat(recent_chat_uuid)
    return chat_tree


async def main():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        chat_repo = ChatRepositoryImpl()
        llm_client = OpenRouterClient(getenv("OPENROUTER_API_KEY"))
        llm_adapter =LLMAdapter(llm_client)
        current_user = UserEntity(
            uuid=str(uuid.uuid4()),
            username="test_user",
            email="test@example.com"
        )
        message_handler = MessageHandler(chat_repo, llm_adapter, current_user)
        chat_tree = ChatTreeEntity()
        selector = ChatSelection(chat_repo, current_user)
        interaction_handler = ChatInteraction(
            message_handler,
            chat_repo,
            chat_tree,
            current_user
            )
        await start_chat(interaction_handler)
        await continue_chat(interaction_handler, "こんにちは")
        await branch_chat(selector, interaction_handler)
        chat_tree = await restart_chat(selector)
        new_handler = ChatInteraction(
            message_handler,
            chat_repo,
            chat_tree,
            current_user
            )
        await continue_chat(new_handler, "こんにちは")
        new_handler.chat_tree._render_tree()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
     asyncio.run(main())
