from anytree import find, NodeMixin

from .message_entity import MessageEntity


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

    def revert_from_dict(self, history: dict) -> None:
        pass
    
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
        