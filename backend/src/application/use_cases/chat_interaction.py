from domain.entities.chat_tree_entity import ChatTreeEntity
from domain.entities.message_entity import MessageEntity
from domain.entities.user_entity import UserEntity
from application.use_cases.services.message_handler import MessageHandler
from application.ports.output.chat_repository import ChatRepositoryProtcol


class ChatInteraction:
    def __init__(
            self,
            message_handler: MessageHandler,
            chat_repository: ChatRepositoryProtcol,
            chat_tree: ChatTreeEntity,
            current_user: UserEntity
            ) -> None:
        "DIいっぱいいっぱい…"
        self.message_handler = message_handler
        self.chat_repository = chat_repository
        self.chat_tree = chat_tree
        self.user= current_user

    async def start_chat(self, initial_message: str) -> None:
        """チャットを開始し、初期システムメッセージでツリーを初期化"""
        initial_message_entity = await self.message_handler.create_initial_message(initial_message)
        self.chat_tree.new_chat(initial_message_entity, owner_uuid=self.user.uuid)
        await self.chat_repository.save_message(initial_message_entity, self.chat_tree, self.user)

    async def send_message_and_get_response(
            self,
            content: str,
            parent_message: MessageEntity,
            llm_model: str
            ) -> MessageEntity:
        """
        ユーザーメッセージ送信とLLM応答を一括処理（アクセス制御付き）

        Args:
            content: メッセージ内容
            parent_message_uuid: 親メッセージのUUID

        Returns:
            MessageEntity: 生成されたアシスタントメッセージ
        """
        # アクセス制御チェック
        if self.chat_tree.owner_uuid != self.user.uuid:
            raise ValueError(
                f"Access denied: user {self.user.uuid} does not own chat {self.chat_tree.uuid}"
            )

        if not self._can_add_message_to(parent_message):
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
    
    def _can_add_message_to(self, parent_message: MessageEntity) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        if self.chat_tree is None:
            return False
        elif not self.chat_tree.root_node.children:#chat開始時
            return True
        else:
            return self.chat_tree.can_add_message_to(parent_message)
