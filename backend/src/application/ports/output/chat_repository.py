from typing import Protocol

from domain.entities.message_entity import MessageEntity

class ChatRepositoryProtcol(Protocol):
    async def save_message(self, message_entity: MessageEntity) -> None:
        pass

    # async def load_chat_history(self, uuid_history: list[MessageEntity]) -> list[dict]:
    #     print("this is protocol, not implement")
    #     return []
