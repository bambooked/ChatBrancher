from abc import ABC, abstractmethod

from domain.entities.message_entity import MessageEntity
from domain.entities.chat_tree_entity import ChatTreeEntity

class ChatRepositoryProtcol(ABC):
    @abstractmethod
    async def save_message(
        self,
        message_entity: MessageEntity,
        chat_tree:ChatTreeEntity | None = None,
        user_context_id: str | None = None
        ) -> None:
        ""
        pass
    
    @abstractmethod
    async def save_assistant_message_detail(
        self,
        message_uuid: str,
        llm_details: dict
        ) -> None:
        ""
        pass
    
    @abstractmethod
    async def get_chat_tree_messages(
        self,
        chat_tree_id: str
        ) -> list[dict] | None:
        ""
        pass

    
    @abstractmethod
    async def get_all_chat_tree_ids(self) -> list[str]:
        """
        全てのチャットツリーIDを取得（開発用 - 本番では認証が必要）
        
        Returns:
            list[str]: 存在する全チャットツリーIDのリスト
        """
        pass
    