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
load_dotenv()

async def start_chat(interaction_handler: ChatInteraction) -> None:
    await interaction_handler.start_chat(
        initial_message="あなたは優秀なアシスタントです。userは日本語の回答を期待しています。"
        )
    print(interaction_handler.chat_tree.root_node.message.content)
    interaction_handler.chat_tree._render_tree()

async def continue_chat(
        interaction_handler: ChatInteraction,
        ) -> None:
    parent_message = interaction_handler.chat_tree.root_node.message
    resp = await interaction_handler.send_message_and_get_response(
        content="こんにちは",
        parent_message=parent_message,
        llm_model="anthropic/claude-3-haiku"
    )
    print(resp)
    pass

async def branch_chat() -> None:
    pass


async def main():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        chat_repo = ChatRepositoryImpl()
        llm_client = OpenRouterClient(getenv("OPENROUTER_API_KEY"))
        llm_adapter =LLMAdapter(llm_client)
        current_user = UserEntity(str(uuid.uuid4()))
        message_handler = MessageHandler(chat_repo, llm_adapter, current_user)
        chat_tree = ChatTreeEntity()
        interaction_handler = ChatInteraction(
            message_handler,
            chat_repo,
            chat_tree,
            current_user
            )
        await start_chat(interaction_handler)
        await continue_chat(interaction_handler)
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
     asyncio.run(main())
