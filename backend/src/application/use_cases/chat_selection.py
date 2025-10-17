from uuid import UUID

from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.domain.entities.user_entity import UserEntity
from src.application.ports.output.chat_repository import ChatRepositoryProtcol

class ChatSelection:
    def __init__(
            self,
            chat_repository: ChatRepositoryProtcol,
            current_user: UserEntity
            ) -> None:
        self.chat_repository = chat_repository
        self.user = current_user

    async def restart_chat(self, chat_uuid: str) -> ChatTreeEntity:
        """チャットを再開する（アクセス制御付き）"""
        # 1. チャット情報をDBから取得
        chat_info = await self.chat_repository.get_chat_tree_info(chat_uuid)
        if not chat_info:
            raise ValueError(f"Chat tree with ID {chat_uuid} not found")

        # 2. アクセス制御チェック
        if chat_info["owner_uuid"] != self.user.uuid:
            raise ValueError(
                f"Access denied: user {self.user.uuid} does not own chat {chat_uuid}"
            )

        # 3. メッセージリスト取得
        message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid, self.user)

        # 4. ツリー復元（DBから取得した正しいowner_uuidで）
        self.chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
        self.chat_tree.uuid = UUID(chat_uuid)
        self.chat_tree.owner_uuid = chat_info["owner_uuid"]  # 修正：DBから取得
        return self.chat_tree
    
    async def get_chat_tree(self, chat_uuid: str) -> ChatTreeEntity:
        """指定されたチャットツリーを取得（アクセス制御付き、現在のインスタンスを変更せずに返す）"""
        # 1. チャット情報をDBから取得
        chat_info = await self.chat_repository.get_chat_tree_info(chat_uuid)
        if not chat_info:
            raise ValueError(f"Chat tree with ID {chat_uuid} not found")

        # 2. アクセス制御チェック
        if chat_info["owner_uuid"] != self.user.uuid:
            raise ValueError(
                f"Access denied: user {self.user.uuid} does not own chat {chat_uuid}"
            )

        # 3. メッセージリスト取得
        message_list = await self.chat_repository.get_chat_tree_messages(chat_uuid, self.user)

        # 4. ツリー復元（DBから取得した正しいowner_uuidで）
        chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
        chat_tree.uuid = UUID(chat_uuid)
        chat_tree.owner_uuid = chat_info["owner_uuid"]  # 修正：DBから取得
        return chat_tree


    async def get_all_chat_uuid(self) -> list[str]:
        uuids = await self.chat_repository.get_all_chat_tree_ids(self.user)
        return uuids