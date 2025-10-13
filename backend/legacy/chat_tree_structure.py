from anytree import AnyNode, find
from typing import Dict, Any, Optional

class ChatStructure(AnyNode):
    def __init__(self, message_uuid: str, parent: Optional['ChatStructure'] = None) -> None:
        super().__init__(parent=parent, message_uuid=message_uuid)
        self.message_uuid: str = message_uuid

    def append_message(self, parent_message_uuid: str, message_uuid: str) -> None:
        parent = self.pick_message_from_uuid(parent_message_uuid)
        ChatStructure(message_uuid=message_uuid, parent=parent)

    def load_flatten_history(self, target_message_uuid) -> list[str]:
        selected_node:'ChatStructure' = self.pick_message_from_uuid(target_message_uuid)
        return [node.message_uuid for node in selected_node.path]
    
    def to_dict(self) -> Dict[str, Any]:
        """ツリーをJSON化可能な辞書に変換"""
        return {
            'message_uuid': self.message_uuid,
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], parent: Optional['ChatStructure'] = None) -> 'ChatStructure':
        """辞書からツリーを復元"""
        node = cls(message_uuid=data['message_uuid'], parent=parent)
        for child_data in data.get('children', []):
            cls.from_dict(child_data, parent=node)
        return node
        
    def pick_message_from_uuid(self, uuid: str) -> 'ChatStructure':
        # anytreeのfind関数を使用
        found = find(self.root, lambda node: node.message_uuid == uuid)
        if not found:
            raise ValueError("条件に一致するノードが見つかりませんでした。")
        return found