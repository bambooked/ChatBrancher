from application.ports.output.chat_repository import ChatRepositoryProtcol
from domain.entities.message_entity import MessageEntity
from domain.entities.chat_tree_entity import ChatTreeEntity
from infrastructure.models import MessageModel, AssistantMessageDetail


class ChatRepositoryImpl(ChatRepositoryProtcol):
    def __init__(self) -> None:
        super().__init__()

    
    async def save_message(
            self, 
            message_entity: MessageEntity, 
            chat_tree: ChatTreeEntity| None = None,
            user_context_id: str | None = None) -> None:
        """
        MessageEntityをデータベースに保存
        
        Args:
            message_entity: 保存するメッセージエンティティ
            chat_tree_id: チャット木のID
            parent_uuid: 親メッセージのUUID
            user_context_id: ユーザーコンテキストID
        """
        await MessageModel.create(
            uuid=message_entity.uuid,
            role=message_entity.role,
            content=message_entity.content,
            parent_uuid=parent_uuid,
            chat_tree_id=chat_tree_id,
            user_context_id=user_context_id
        )
    
    async def save_assistant_message_detail(self, message_uuid: str, llm_details: dict) -> None:
        """
        アシスタントメッセージの詳細情報を保存
        
        Args:
            message_uuid: メッセージのUUID
            llm_details: LLMの詳細情報辞書
        """
        message_model = await MessageModel.get(uuid=message_uuid)
        await AssistantMessageDetail.create(
            message=message_model,
            provider=llm_details.get('provider'),
            model_name=llm_details.get('model'),
            prompt_tokens=llm_details.get('prompt_tokens', 0),
            completion_tokens=llm_details.get('completion_tokens', 0),
            total_tokens=llm_details.get('total_tokens', 0),
            temperature=llm_details.get('temperature'),
            max_tokens=llm_details.get('max_tokens'),
            finish_reason=llm_details.get('finish_reason'),
            gen_id=llm_details.get('gen_id'),
            object_=llm_details.get('object_'),
            created_timestamp=llm_details.get('created')
        )
    
    async def get_chat_tree_messages(self, chat_tree_id: str) -> list[dict]:
        """
        指定したチャット木IDに属する全てのメッセージを一括取得
        
        Args:
            chat_tree_id: チャット木のID
            
        Returns:
            list[dict]: 木構造復元に必要な情報を含むメッセージ辞書のリスト
                       各辞書は uuid, parent_uuid, role, content, created_at を含む
        """
        message_models = await MessageModel.filter(chat_tree_id=chat_tree_id).order_by('created_at')
        return [
            {
                'uuid': str(model.uuid),
                'parent_uuid': str(model.parent_uuid) if model.parent_uuid else None,
                'role': model.role.value,
                'content': model.content,
                'created_at': model.created_at.isoformat()
            }
            for model in message_models
        ]

    
    async def get_all_chat_tree_ids(self) -> list[str]:
        """
        全てのチャットツリーIDを取得（開発用 - 本番では認証が必要）
        
        Returns:
            list[str]: 存在する全チャットツリーIDのリスト（重複なし）
        """
        message_models = await MessageModel.all().distinct().values_list('chat_tree_id', flat=True)
        return [str(chat_tree_id) for chat_tree_id in message_models if chat_tree_id]
    