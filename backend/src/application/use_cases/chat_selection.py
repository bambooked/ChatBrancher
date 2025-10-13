from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity
from application.ports.output.chat_repository import ChatRepositoryProtcol

class ChatSelection:
    def __init__(
            self,
            chat_repository: ChatRepositoryProtcol,
            current_user: UserEntity
            ) -> None:
        self.chat_repository = chat_repository
        self.user = current_user

    async def restart_chat(self, chat_uuid: str) -> ChatTreeEntity:
        """チャットを再開する"""
        message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid, self.user)
        if not message_list:
            raise ValueError(f"Chat tree with ID {chat_uuid} not found")
        
        # メッセージリストからチャットツリーを復元
        self.chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
        return self.chat_tree
    
    # async def get_chat_tree(self, chat_uuid: str) -> ChatTreeEntity:
    #     """指定されたチャットツリーを取得（現在のインスタンスを変更せずに返す）"""
    #     message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid)
    #     if not message_list:
    #         raise ValueError(f"Chat tree with ID {chat_uuid} not found")
        
    #     # 新しいインスタンスとして復元して返す
    #     return ChatTreeEntity.restore_from_message_list(message_list)
