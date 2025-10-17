from src.application.ports.output.chat_repository import ChatRepositoryProtcol
from src.application.ports.input.llm_adapter import LLMCAdapterProtcol
from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.domain.entities.message_entity import MessageEntity
from src.domain.entities.user_entity import UserEntity

class MessageHandler:
    """
    メッセージのやりとり全般を担当するユースケース
    
    あらゆる種類のメッセージ（USER/ASSISTANT/SYSTEM）の生成・保存・ツリー追加を統一的に処理。
    LLMは外部サービスとして扱い、応答生成のみ委譲する。
    """
    
    def __init__(
            self,
            repo: ChatRepositoryProtcol,
            llm_client: LLMCAdapterProtcol,
            current_user: UserEntity
            ) -> None:
        self.repo = repo
        self.llm_client = llm_client
        self.user = current_user

    async def create_initial_message(
            self,
            content: str|None,
        ) -> MessageEntity:
        """
        システムメッセージエンティティを作成（保存はしない）
        注意：強制的にsystemメッセージとなる。
        
        Args:
            content: メッセージ内容
            
        Returns:
            MessageEntity: 作成されたシステムメッセージ
        """
        if not content:
            content = ""
        message = MessageEntity.create_system_message(content)
        return message
        
    async def add_user_message(
        self, 
        chat_tree: ChatTreeEntity, 
        content: str, 
        parent_message: MessageEntity,
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
        chat_tree.add_message(parent_message, message)
        await self.repo.save_message(message, chat_tree, self.user)
        return message
    
    async def add_assistant_message(
        self, 
        chat_tree: ChatTreeEntity, 
        content: str, 
        parent_message: MessageEntity,
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
        chat_tree.add_message(parent_message, message)
        await self.repo.save_message(message, chat_tree, self.user)
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
        chat_tree.add_message(parent_message, message)
        await self.repo.save_message(message, chat_tree, self.user)
        return message
    
    async def generate_llm_response(
        self,
        chat_tree: ChatTreeEntity,
        user_message: MessageEntity,
        llm_model: str,
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

        # AssistantMessageDetailを保存（生のAPIレスポンスを使用）
        raw_response = llm_response.get('raw_response', llm_response)
        await self.repo.save_assistant_message_detail(
            llm_message_entity,
            raw_response,
            self.user
        )

        # アシスタントメッセージとして追加
        return llm_message_entity