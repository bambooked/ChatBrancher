"""
チャットツリー復元のためのヘルパー関数群
"""
from typing import Dict, List, Optional, Any
from anytree import AnyNode

from src.domain.entities.message_entity import MessageEntity, Role
from src.domain.entities.chat_tree_entity import MessageNode


def convert_parent_uuid_to_children_format(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    parent_uuid形式のメッセージリストをchildren形式（anytree用）に変換
    
    Args:
        messages: parent_uuidを含むメッセージ辞書のリスト
        
    Returns:
        children形式に変換されたルートノード辞書、ルートが見つからない場合はNone
        
    Raises:
        ValueError: 循環参照が検出された場合
    """
    if not messages:
        return None
    
    # UUIDマップを作成
    uuid_map = {msg['uuid']: dict(msg) for msg in messages}
    
    # 各メッセージにchildren配列を初期化
    for msg_dict in uuid_map.values():
        msg_dict['children'] = []
    
    # parent_uuidを使ってchildren配列を構築
    root_node = None
    
    for msg in messages:
        msg_uuid = msg['uuid']
        parent_uuid = msg.get('parent_uuid')
        
        if parent_uuid is None:
            # ルートノード
            if root_node is not None:
                raise ValueError("Multiple root nodes found")
            root_node = uuid_map[msg_uuid]
        else:
            # 子ノード
            parent = uuid_map.get(parent_uuid)
            if parent is None:
                raise ValueError(f"Parent with UUID {parent_uuid} not found for message {msg_uuid}")
            
            parent['children'].append(uuid_map[msg_uuid])
    
    if root_node is None:
        raise ValueError("No root node found (no message with parent_uuid=None)")
    
    # parent_uuidフィールドを削除（anytreeでは不要）
    _remove_parent_uuid_recursively(root_node)
    
    return root_node


def _remove_parent_uuid_recursively(node: Dict[str, Any]) -> None:
    """再帰的にparent_uuidフィールドを削除"""
    node.pop('parent_uuid', None)
    for child in node.get('children', []):
        _remove_parent_uuid_recursively(child)


def convert_anytree_to_message_node(anytree_node: AnyNode):
    """
    anytreeのAnyNodeをMessageNodeに変換
    
    Args:
        anytree_node: 変換元のAnyNode
        
    Returns:
        変換されたMessageNode
    """
    # MessageEntityを作成
    message_entity = MessageEntity(
        uuid=anytree_node.uuid,
        role=Role(anytree_node.role),
        content=anytree_node.content
    )
    
    # MessageNodeを作成
    message_node = MessageNode(parent=None, message=message_entity)
    
    # 子ノードを再帰的に変換して追加
    for child_anytree in anytree_node.children:
        child_message_node = convert_anytree_to_message_node(child_anytree)
        child_message_node.parent = message_node
    
    return message_node