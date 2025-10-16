from abc import ABC, abstractmethod

from domain.entities.message_entity import MessageEntity
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity

class ChatRepositoryProtcol(ABC):
    @abstractmethod
    async def save_message(
        self,
        message_entity: MessageEntity,
        chat_tree: ChatTreeEntity,
        current_user: UserEntity
        ) -> None:
        "渡されたmessageを参考にして、chat_treeから自動的にparentを取得して隣接リストで保存する。"
        pass
    
    @abstractmethod
    async def save_assistant_message_detail(
        self,
        related_message: MessageEntity,
        llm_details: dict,
        current_user: UserEntity
        ) -> None:
        ""
        pass
    
    @abstractmethod
    async def get_chat_tree_messages(
        self,
        chat_tree_id: str,
        current_user: UserEntity
        ) -> list[dict] | None:
        ""
        pass

    @abstractmethod
    async def get_all_chat_tree_ids(
        self,
        current_user: UserEntity
        ) -> list[str]:
        "指定したユーザーに紐づく全てのチャットツリーIDを取得"
        pass

    @abstractmethod
    async def get_chat_tree_info(self, chat_uuid: str) -> dict | None:
        """チャットツリーのメタ情報（owner_uuid含む）を取得"""
        pass
