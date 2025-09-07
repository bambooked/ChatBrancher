from typing import Protocol

from domain.entities.message_entity import MessageEntity

class ChatRepositoryProtcol(Protocol):
    async def save_message(self, message_entity: MessageEntity, chat_tree_id: str, parent_uuid: str | None = None, user_context_id: str | None = None) -> None:
        pass
    
    async def save_assistant_message_detail(self, message_uuid: str, llm_details: dict) -> None:
        pass
    
    async def get_chat_tree_messages(self, chat_tree_id: str) -> list[dict] | None:
        pass

    
    async def get_all_chat_tree_ids(self) -> list[str]:
        """
        全てのチャットツリーIDを取得（開発用 - 本番では認証が必要）
        
        Returns:
            list[str]: 存在する全チャットツリーIDのリスト
        """
        pass
    