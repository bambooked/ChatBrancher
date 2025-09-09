from application.ports.output.chat_repository import ChatRepositoryProtcol
from application.ports.input.llm_adapter import LLMCAdapterProtcol
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.message_entity import MessageEntity

class MessageHandler:
    """
    メッセージのやりとり全般を担当するユースケース
    
    あらゆる種類のメッセージ（USER/ASSISTANT/SYSTEM）の生成・保存・ツリー追加を統一的に処理。
    LLMは外部サービスとして扱い、応答生成のみ委譲する。
    """
    
    def __init__(self, repo: ChatRepositoryProtcol, llm_client: LLMCAdapterProtcol) -> None:
        self.repo = repo
        self.llm_client = llm_client

    async def create_system_message(
            self,
            content: str,
            chat_tree_id: str,
            user_context_id: str|None = None
        ) -> MessageEntity:
        """
        
        """
        message = MessageEntity.create_system_message(content)
        await self.repo.save_message(message)
        return message
        
    async def add_user_message(
        self, 
        chat_tree: ChatTreeEntity, 
        content: str, 
        parent_message: MessageEntity,
        chat_tree_id: str,
        user_context_id: str|None = None
    ) -> MessageEntity:
        """
        ユーザーメッセージを作成・保存・ツリーに追加
        
        Args:
            tree: 対象のチャットツリー
            content: メッセージ内容
            parent_uuid: 親メッセージのUUID
            
        Returns:
            MessageEntity: 作成されたユーザーメッセージ
        """
        message = MessageEntity.create_user_message(content)
        await self.repo.save_message(message)
        chat_tree.add_message(parent_message, message)
        return message
    
    async def add_assistant_message(
        self, 
        chat_tree: ChatTreeEntity, 
        content: str, 
        parent_message: MessageEntity,
        chat_tree_id: str,
        user_context_id: str|None = None
    ) -> MessageEntity:
        """
        アシスタントメッセージを作成・保存・ツリーに追加
        
        Args:
            tree: 対象のチャットツリー
            content: メッセージ内容
            parent_uuid: 親メッセージのUUID
            
        Returns:
            MessageEntity: 作成されたアシスタントメッセージ
        """
        message = MessageEntity.create_assistant_message(content)
        await self.repo.save_message(message)
        chat_tree.add_message(parent_message, message)
        return message
    
    async def add_system_message(
        self, 
        chat_tree: ChatTreeEntity, 
        content: str, 
        parent_message: MessageEntity
    ) -> MessageEntity:
        """
        システムメッセージを作成・保存・ツリーに追加
        
        Args:
            tree: 対象のチャットツリー
            content: メッセージ内容
            parent_uuid: 親メッセージのUUID
            
        Returns:
            MessageEntity: 作成されたシステムメッセージ
        """
        message = MessageEntity.create_system_message(content)
        await self.repo.save_message(message)
        chat_tree.add_message(parent_message, message)
        return message
    
    async def generate_llm_response(
        self, 
        chat_tree: ChatTreeEntity, 
        user_message: MessageEntity,
        llm_model: str,
        chat_tree_id: str,
        user_context_id: str|None = None
    ) -> MessageEntity:
        """
        LLMからの応答を生成してアシスタントメッセージとして追加
        
        Args:
            tree: 対象のチャットツリー
            user_message_uuid: 応答対象のユーザーメッセージUUID
            
        Returns:
            MessageEntity: 生成されたアシスタントメッセージ
            
        Raises:
            ValueError: ユーザーメッセージが見つからない場合
            LLMClientError: LLM呼び出しに失敗した場合
        """
        # 会話履歴を取得
        conversation_history = chat_tree.get_conversation_path(user_message)
        # conversation_history = await self.repo.load_chat_history(message_uuid_list)
        
        # LLMから応答を取得
        llm_response = await self.llm_client.get_response(
            conversation_history,
            llm_model
            )

        llm_message_entity = await self.add_assistant_message(chat_tree, llm_response["content"], user_message)
        
        # アシスタントメッセージとして追加
        return llm_message_entity