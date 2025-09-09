from typing import List, Dict, Any
from anytree import find, NodeMixin
from anytree.importer import DictImporter

from domain.entities.message_entity import MessageEntity
from domain.services.tree_reconstruction import (
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
        pass

    def create_new(self, initial_message: MessageEntity) -> None:
        self.root_node = MessageNode(parent=None, message = initial_message)

    def pick_message_from_uuid(self, root_node: MessageNode, message: MessageEntity) -> MessageNode:
        found = find(root_node, lambda node :str(node.message.uuid) == str(message.uuid))
        if not found:
            raise ValueError("Not Found Node has provided conditon")
        return found
    
    def add_message(self, parent_message: MessageEntity, message: MessageEntity) -> None:
        """メッセージをツリーに追加"""
        parent_node = self.pick_message_from_uuid(self.root_node, parent_message)
        MessageNode(parent=parent_node, message = message)
    
    def get_conversation_path(self, target_message: MessageEntity) -> list[MessageEntity]:
        """指定メッセージまでの会話履歴パスを取得"""
        selected_node = self.pick_message_from_uuid(self.root_node, target_message)
        path = [node.message for node in selected_node.path]
        return path
    
    def can_add_message_to(self, parent_message: MessageEntity) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        try:
            self.pick_message_from_uuid(self.root_node, parent_message)
            return True
        except ValueError:
            return False
    
    @classmethod
    def restore_from_message_list(cls, messages: List[Dict[str, Any]]) -> 'ChatTreeEntity':
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
        