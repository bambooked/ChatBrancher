from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.message_entity import MessageEntity
from application.use_cases.services.message_handler import MessageHandler


class ChatInteraction:
    def __init__(
            self,
            message_handler: MessageHandler,
            chat_repository,
            user_context_id: str|None = None
            ) -> None:
        self.message_handler = message_handler
        self.chat_repository = chat_repository
        self.chat_tree = ChatTreeEntity()

    async def start_chat(self, initial_message: str) -> ChatTreeEntity:
        """チャットを開始し、初期システムメッセージでツリーを初期化"""
        initial_message_entity = await self.message_handler.create_system_message(initial_message)
        self.chat_tree.create_new(initial_message_entity)
        return self.chat_tree

    async def restart_chat(self, chat_uuid: str) -> ChatTreeEntity:
        """チャットを再開する"""
        message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid)
        if not message_list:
            raise ValueError(f"Chat tree with ID {chat_uuid} not found")
        
        # メッセージリストからチャットツリーを復元
        self.chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
        return self.chat_tree
        

    async def send_message_and_get_response(
            self,
            content: str,
            parent_message: MessageEntity,
            llm_model: str
            ) -> MessageEntity:
        """
        ユーザーメッセージ送信とLLM応答を一括処理（メイン機能）
        
        Args:
            content: メッセージ内容
            parent_message_uuid: 親メッセージのUUID
            
        Returns:
            MessageEntity: 生成されたアシスタントメッセージ
        """
        if not self.can_add_message_to(parent_message):
            raise ValueError(f"Cannot add message to parent {parent_message.uuid}")
        
        # ユーザーメッセージ追加
        user_message = await self.message_handler.add_user_message(
            self.chat_tree, content, parent_message
        )
        llm_responce = await self.message_handler.generate_llm_response(
            self.chat_tree,
            user_message,
            llm_model
        )
        
        # LLM応答生成
        return llm_responce
    
    def can_add_message_to(self, parent_message: MessageEntity) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        if self.chat_tree is None:
            return False
        return self.chat_tree.can_add_message_to(parent_message)
    
    async def get_chat_list(self) -> list[str]:
        """全チャット一覧を取得（開発用 - 本番では認証が必要）"""
        return await self.chat_repository.get_all_chat_tree_ids()
    
    async def get_chat_tree(self, chat_uuid: str) -> ChatTreeEntity:
        """指定されたチャットツリーを取得（現在のインスタンスを変更せずに返す）"""
        message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid)
        if not message_list:
            raise ValueError(f"Chat tree with ID {chat_uuid} not found")
        
        # 新しいインスタンスとして復元して返す
        return ChatTreeEntity.restore_from_message_list(message_list)
    
    @property
    def uuid(self) -> str|None:
        """チャットツリーのUUIDを取得"""
        return self.chat_tree_id
