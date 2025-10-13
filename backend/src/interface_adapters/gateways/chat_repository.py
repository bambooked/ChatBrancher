from application.ports.output.chat_repository import ChatRepositoryProtcol
from domain.entities.message_entity import MessageEntity
from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.user_entity import UserEntity
from infrastructure.db.models import MessageModel, AssistantMessageDetail, ChatTreeDetail


class ChatRepositoryImpl(ChatRepositoryProtcol):
    def __init__(self) -> None:
        super().__init__()

    async def ensure_chat_tree_detail(self, chat_tree: ChatTreeEntity) -> ChatTreeDetail:
        """
        ChatTreeEntityに対応するChatTreeDetailがなければ作成する
        """
        chat_tree_detail, created = await ChatTreeDetail.get_or_create(uuid=chat_tree.uuid)
        return chat_tree_detail

    
    async def save_message(
            self,
            message_entity: MessageEntity,
            chat_tree: ChatTreeEntity,
            current_user: UserEntity,
            ) -> None:
        """
        Messageをデータベースに保存
        """
        chat_tree_detail = await self.ensure_chat_tree_detail(chat_tree)

        parent_message_model = None
        if chat_tree.root_node is not None:
            try:
                # message_entity自身をツリーから検索
                message_node = chat_tree.pick_message_from_uuid(chat_tree.root_node, message_entity)

                # その親ノードを取得（重要：.parentでアクセス）
                if message_node.parent is not None:
                    parent_uuid = message_node.parent.message.uuid
                    parent_message_model = await MessageModel.get(uuid=parent_uuid)
                # message_node.parentがNoneの場合は、parent_message_modelはNoneのまま（ルートノード）
            except ValueError:
                # message_entityがツリーに見つからない場合
                parent_message_model = None

        await MessageModel.create(
            uuid=message_entity.uuid,
            role=message_entity.role,
            content=message_entity.content,
            parent=parent_message_model,
            chat_tree=chat_tree_detail,
            user_context_id=current_user.uuid
        )
    
    async def save_assistant_message_detail(
            self,
            related_message: MessageEntity,
            llm_details: dict,
            current_user: UserEntity
            ) -> None:
        """
        アシスタントメッセージの詳細情報を保存
        """
        # 関連するMessageModelを取得
        message_model = await MessageModel.get(uuid=related_message.uuid)

        # AssistantMessageDetailを作成
        await AssistantMessageDetail.create(
            message=message_model,
            provider=llm_details.get("provider"),
            model_name=llm_details.get("model"),
            prompt_tokens=llm_details.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=llm_details.get("usage", {}).get("completion_tokens", 0),
            total_tokens=llm_details.get("usage", {}).get("total_tokens", 0),
            temperature=llm_details.get("temperature"),
            max_tokens=llm_details.get("max_tokens"),
            finish_reason=llm_details.get("finish_reason"),
            gen_id=llm_details.get("id"),
            object_=llm_details.get("object"),
            created_timestamp=llm_details.get("created")
        )
    
    async def get_chat_tree_messages(
            self,
            chat_tree_id: str,
            current_user: UserEntity
            ) -> list[dict]:
        """
        指定したチャット木IDに属する全てのメッセージを一括取得
        """
        return []

    async def get_all_chat_tree_ids(
            self,
            current_user: UserEntity
            ) -> list[str]:
        """
        指定したユーザーに紐づく全てのチャットツリーIDを取得
        """
        # ユーザーに紐づくメッセージから一意のチャットツリーIDを取得
        messages = await MessageModel.filter(
            user_context_id=current_user.uuid
        ).prefetch_related("chat_tree")

        # 重複を除いてチャットツリーIDのリストを作成
        chat_tree_ids = list(set([str(msg.chat_tree.uuid) for msg in messages]))

        return chat_tree_ids