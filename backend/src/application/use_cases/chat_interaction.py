from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.message_entity import MessageEntity
from .servises.message_handler import MessageHandler


class ChatInteraction:
    def __init__(self, message_handler: MessageHandler) -> None:
        self.message_handler = message_handler
        self.chat_tree: ChatTreeEntity = None

    async def start_chat(self, initial_message: str) -> ChatTreeEntity:
        """チャットを開始し、初期システムメッセージでツリーを初期化"""
        initial_message_entity = await self.message_handler.create_system_message(initial_message)
        self.chat_tree = ChatTreeEntity.create_new(initial_message_entity.uuid)
        return self.chat_tree

    async def restart_chat(self, chat_uuid) -> None:
        pass

    async def send_message_and_get_response(self, content: str, parent_message_uuid: str) -> MessageEntity:
        """
        ユーザーメッセージ送信とLLM応答を一括処理（メイン機能）
        
        Args:
            content: メッセージ内容
            parent_message_uuid: 親メッセージのUUID
            
        Returns:
            MessageEntity: 生成されたアシスタントメッセージ
        """
        if not self.can_add_message_to(parent_message_uuid):
            raise ValueError(f"Cannot add message to parent {parent_message_uuid}")
        
        # ユーザーメッセージ追加
        user_message = await self.message_handler.add_user_message(
            self.chat_tree, content, parent_message_uuid
        )
        
        # LLM応答生成
        return await self.message_handler.generate_llm_response(
            self.chat_tree, user_message.uuid
        )
    
    def can_add_message_to(self, parent_uuid: str) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        if self.chat_tree is None:
            return False
        return self.chat_tree.can_add_message_to(parent_uuid)