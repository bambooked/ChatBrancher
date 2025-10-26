from typing import Any, Optional
from uuid import UUID

from anytree import find, NodeMixin
from anytree.importer import DictImporter

from src.domain.entities.message_entity import MessageEntity
from src.domain.services.tree_reconstruction import (
    convert_parent_uuid_to_children_format,
    convert_anytree_to_message_node
)


class MessageNode(NodeMixin):
    def __init__(self, message: MessageEntity, parent=None) -> None:
        super().__init__()
        self.parent = parent
        self.message: MessageEntity = message

class ChatTreeEntity:
    """
    チャットの会話ツリーを管理するドメインエンティティ
    """
    def __init__(self) -> None:
        self.uuid: Optional[UUID] = None
        self.root_node: Optional[MessageNode] = None
        self.owner_uuid: Optional[str] = None

    def new_chat(
        self,
        initial_message: MessageEntity,
        *,
        owner_uuid: str,
        chat_uuid: UUID | str,
    ) -> None:
        self.root_node = MessageNode(parent=None, message=initial_message)
        self.uuid = UUID(str(chat_uuid))
        self.owner_uuid = owner_uuid

    def revert_chat(self, chat_uuid: str, messages: list[dict[str, Any]], owner_uuid: str) -> None:
        self.restore_from_message_list(messages)
        self.uuid = UUID(str(chat_uuid))
        self.owner_uuid = owner_uuid

    def is_owned_by(self, user_uuid: str) -> bool:
        """指定されたユーザーがこのチャットの所有者かどうかを判定"""
        return self.owner_uuid == user_uuid

    def get_message_node_by_uuid(self, message_uuid: str | UUID) -> MessageNode:
        """UUID からメッセージノードを取得"""
        if self.root_node is None:
            raise ValueError("Chat tree is empty")

        target_uuid = str(message_uuid)
        found = find(self.root_node, lambda node: str(node.message.uuid) == target_uuid)
        if not found:
            raise ValueError(f"Message with UUID {target_uuid} not found")
        return found

    def get_message_by_uuid(self, message_uuid: str | UUID) -> MessageEntity:
        """UUID から MessageEntity を取得"""
        return self.get_message_node_by_uuid(message_uuid).message

    def add_message(self, parent_message: MessageEntity, message: MessageEntity) -> None:
        """メッセージをツリーに追加"""
        parent_node = self.get_message_node_by_uuid(parent_message.uuid)
        MessageNode(parent=parent_node, message = message)

    def get_conversation_path(self, target_message: MessageEntity) -> list[MessageEntity]:
        """指定メッセージまでの会話履歴パスを取得"""
        selected_node = self.get_message_node_by_uuid(target_message.uuid)
        path = [node.message for node in selected_node.path]
        return path

    def can_add_message_to(self, parent_message: MessageEntity) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        try:
            self.get_message_node_by_uuid(parent_message.uuid)
            return True
        except ValueError:
            return False
    
    @classmethod
    def restore_from_message_list(cls, messages: list[dict[str, Any]]) -> 'ChatTreeEntity':
        """
        メッセージリスト（parent_uuid形式）からChatTreeEntityを復元
        
        Args:
            messages: parent_uuidを含むメッセージ辞書のリスト
            
        Returns:
            復元されたChatTreeEntity
            
        Raises:
            ValueError: データ形式が不正な場合
        """
        if not messages:
            raise ValueError("Messages list is empty")
        
        # parent_uuid形式からchildren形式に変換
        root_dict = convert_parent_uuid_to_children_format(messages)
        if root_dict is None:
            raise ValueError("Could not find root node")
        
        # anytreeで木構造を構築
        importer = DictImporter()
        anytree_root = importer.import_(root_dict)
        
        # MessageNodeに変換
        message_root = convert_anytree_to_message_node(anytree_root)
        
        # ChatTreeEntityを構築
        chat_tree = cls()
        chat_tree.root_node = message_root
        
        return chat_tree
        
    def _render_tree(self):
        from anytree.render import RenderTree
        for pre, _, node in RenderTree(self.root_node):
            print("%s%s" % (pre, node.message.content))
