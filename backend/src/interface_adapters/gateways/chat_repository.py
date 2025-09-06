from src.application.ports.output.chat_repository import ChatRepositoryProtcol
from src.domain.entities.message_entity import MessageEntity
from src.infrastructure.models import MessageModel


class ChatRepositoryImpl(ChatRepositoryProtcol):
    def __init__(self) -> None:
        super().__init__()

    
    async def save_message(self, message_entity: MessageEntity) -> None:
        """
        MessageEntityをデータベースに保存
        
        Args:
            message_entity: 保存するメッセージエンティティ
        """
        await MessageModel.create(
            uuid=message_entity.uuid,
            role=message_entity.role,
            content=message_entity.content
        )
    