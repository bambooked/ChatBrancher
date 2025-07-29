from dataclasses import dataclass
import uuid
from typing import List

from ..services.chat_tree_structure import ChatStructure


@dataclass
class ChatTreeEntity:
    """
    チャットの会話ツリーを管理するドメインエンティティ
    
    ChatStructure（技術的実装）への合理的なインターフェースを提供し、
    ビジネスロジックとツリー操作を適切に分離する。
    """
    tree_uuid: str
    structure: ChatStructure

    @classmethod
    def create_new(cls, root_message_uuid: str) -> 'ChatTreeEntity':
        """新しいツリーを作成"""
        root_structure = ChatStructure(message_uuid=root_message_uuid)
        return cls(
            tree_uuid=str(uuid.uuid4()),
            structure=root_structure
        )
    
    def add_message(self, parent_message_uuid: str, message_uuid: str) -> None:
        """メッセージをツリーに追加"""
        self.structure.append_message(parent_message_uuid, message_uuid)
    
    def get_conversation_path(self, target_message_uuid: str) -> List[str]:
        """指定メッセージまでの会話履歴パスを取得"""
        return self.structure.load_flatten_history(target_message_uuid)
    
    def find_message_node(self, message_uuid: str):
        """指定UUIDのメッセージノードを取得"""
        return self.structure.pick_message_from_uuid(message_uuid)
    
    
    def can_add_message_to(self, parent_uuid: str) -> bool:
        """指定の親にメッセージを追加可能かチェック"""
        try:
            self.find_message_node(parent_uuid)
            return True
        except ValueError:
            return False