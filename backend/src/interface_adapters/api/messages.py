from uuid import UUID
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.infrastructure.db.models import UserModel, ChatTreeDetail
from src.interface_adapters.api.auth import get_current_user
from src.application.use_cases.chat_selection import ChatSelection
from src.application.use_cases.chat_interaction import ChatInteraction
from src.interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from src.application.use_cases.services.message_handler import MessageHandler
from src.domain.entities.user_entity import UserEntity
from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.interface_adapters.gateways.llm_api_adapter import LLMAdapter
from src.infrastructure.openrouter_client import OpenRouterClient
from src.infrastructure.config import settings

router = APIRouter(prefix="/api/v1/chats", tags=["messages"])


# 依存性注入: シングルトンとして管理
@lru_cache()
def get_chat_repository() -> ChatRepositoryImpl:
    """チャットリポジトリのシングルトンインスタンスを取得"""
    return ChatRepositoryImpl()


@lru_cache()
def get_llm_adapter() -> LLMAdapter:
    """LLMアダプターのシングルトンインスタンスを取得"""
    llm_client = OpenRouterClient(api_key=settings.OPENROUTER_API_KEY)
    return LLMAdapter(llm_client=llm_client)


class SendMessageRequest(BaseModel):
    """メッセージ送信リクエスト"""

    content: str
    parent_message_uuid: str | None = None
    llm_model: str = "anthropic/claude-3-haiku"


class MessageResponse(BaseModel):
    """メッセージレスポンス"""

    uuid: str
    role: str
    content: str
    parent_uuid: str | None


class SendMessageResponse(BaseModel):
    """メッセージ送信レスポンス"""

    user_message: MessageResponse
    assistant_message: MessageResponse


@router.post("/{chat_uuid}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_uuid: UUID,
    request: SendMessageRequest,
    current_user: UserModel = Depends(get_current_user),
    chat_repository: ChatRepositoryImpl = Depends(get_chat_repository),
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
):
    # --- チャットの存在・権限チェック ---
    chat = await ChatTreeDetail.filter(uuid=chat_uuid).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_uuid != current_user.uuid:
        #raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=404, detail="Chat not found")

    # --- UserEntity ---
    user_entity = UserEntity(
        uuid=str(current_user.uuid),
        username=current_user.username,
        email=current_user.email,
    )

    # --- MessageHandlerとChatSelectionを構築 ---
    message_handler = MessageHandler(
        repo=chat_repository,
        llm_client=llm_adapter,
        current_user=user_entity,
    )
    chat_selection = ChatSelection(chat_repository, user_entity)

    chat_tree = await chat_selection.get_chat_tree(str(chat_uuid))
        
    # --- ChatInteraction の構築 ---
    chat_interaction = ChatInteraction(
        message_handler=message_handler,
        chat_repository=chat_repository,
        chat_tree=chat_tree,
        current_user=user_entity,
    )

    # --- 親メッセージは front が指定 ---
    parent_message_uuid = request.parent_message_uuid
    if parent_message_uuid:
        try:
            chat_tree.get_message_by_uuid(parent_message_uuid)
        except ValueError:
            raise HTTPException(status_code=404, detail="Parent message not found")

    # --- LLM に送信 ---
    try:
        assistant_message = await chat_interaction.send_message_and_get_response(
            content=request.content,
            parent_message_uuid=parent_message_uuid,
            llm_model=request.llm_model,
        )

        assistant_node = chat_tree.get_message_node_by_uuid(assistant_message.uuid)
        if assistant_node.parent is None:
            raise HTTPException(status_code=500, detail="User message not found")
        user_node = assistant_node.parent
        user_message = user_node.message
        user_parent_node = user_node.parent

        return SendMessageResponse(
            user_message=MessageResponse(
                uuid=str(user_message.uuid),
                role=user_message.role.value,
                content=user_message.content,
                parent_uuid=str(user_parent_node.message.uuid) if user_parent_node else None,
            ),
            assistant_message=MessageResponse(
                uuid=str(assistant_message.uuid),
                role=assistant_message.role.value,
                content=assistant_message.content,
                parent_uuid=str(user_message.uuid),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
