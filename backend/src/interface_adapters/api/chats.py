from uuid import uuid4, UUID
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from src.infrastructure.db.models import UserModel, ChatTreeDetail, MessageModel
from src.interface_adapters.api.auth import get_current_user
from src.application.use_cases.chat_interaction import ChatInteraction
from src.application.use_cases.services.message_handler import MessageHandler
from src.interface_adapters.gateways.chat_repository import ChatRepositoryImpl
from src.interface_adapters.gateways.llm_api_adapter import LLMAdapter
from src.infrastructure.openrouter_client import OpenRouterClient
from src.infrastructure.config import settings
from src.domain.entities.chat_tree_entity import ChatTreeEntity
from src.domain.entities.user_entity import UserEntity

router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


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


class ChatResponse(BaseModel):
    """チャットレスポンス"""

    uuid: str
    owner_uuid: str
    created: str
    updated: str


class MessageResponse(BaseModel):
    """メッセージレスポンス"""

    uuid: str
    role: str
    content: str
    parent_uuid: str | None
    created_at: str
    updated_at: str


class ChatTreeResponse(BaseModel):
    """チャットツリーレスポンス"""

    uuid: str
    owner_uuid: str
    created: str
    updated: str
    messages: list[MessageResponse]


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    current_user: UserModel = Depends(get_current_user),
    chat_repository: ChatRepositoryImpl = Depends(get_chat_repository),
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
):
    """
    新しいチャットを作成

    Args:
        current_user: 認証済みユーザー（依存注入）
        chat_repository: チャットリポジトリ（依存注入）
        llm_adapter: LLMアダプター（依存注入）

    Returns:
        ChatResponse: 作成されたチャット情報
    """
    chat_uuid = uuid4()

    # UserEntityを構築
    user_entity = UserEntity(
        uuid=str(current_user.uuid),
        username=current_user.username,
        email=current_user.email,
    )

    # MessageHandlerを構築
    message_handler = MessageHandler(
        repo=chat_repository,
        llm_client=llm_adapter,
        current_user=user_entity,
    )
    chat_tree = ChatTreeEntity()

    # ChatInteractionを構築してstart_chatを実行
    chat_interaction = ChatInteraction(
        message_handler=message_handler,
        chat_repository=chat_repository,
        chat_tree=chat_tree,
        current_user=user_entity,
    )

    # 空の初期メッセージでチャットを開始
    await chat_interaction.start_chat(initial_message="", chat_uuid=chat_uuid)

    # ChatTreeDetailを取得（start_chat内で作成されている）
    chat = await ChatTreeDetail.get(uuid=chat_uuid)

    return ChatResponse(
        uuid=str(chat.uuid),
        owner_uuid=str(chat.owner_uuid),
        created=chat.created.isoformat(),
        updated=chat.updated.isoformat(),
    )


@router.get("", response_model=list[ChatResponse])
async def get_all_chats(current_user: UserModel = Depends(get_current_user)):
    """
    ユーザーの全チャット一覧を取得

    Args:
        current_user: 認証済みユーザー（依存注入）

    Returns:
        list[ChatResponse]: チャット一覧
    """
    chats = await ChatTreeDetail.filter(owner_uuid=current_user.uuid).all()

    return [
        ChatResponse(
            uuid=str(chat.uuid),
            owner_uuid=str(chat.owner_uuid),
            created=chat.created.isoformat(),
            updated=chat.updated.isoformat(),
        )
        for chat in chats
    ]


@router.get("/{chat_uuid}", response_model=ChatTreeResponse)
async def get_chat_tree(
    chat_uuid: UUID, current_user: UserModel = Depends(get_current_user)
):
    """
    特定のチャットツリーを取得

    Args:
        chat_uuid: チャットUUID
        current_user: 認証済みユーザー（依存注入）

    Returns:
        ChatTreeResponse: チャットツリー情報

    Raises:
        HTTPException: チャットが存在しない、またはアクセス権限がない場合
    """
    # チャットを取得
    chat = await ChatTreeDetail.filter(uuid=chat_uuid).first()

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )

    # アクセス権限チェック, セキュリティのために404を返す。
    if chat.owner_uuid != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )

    # メッセージを取得
    messages = await MessageModel.filter(chat_tree=chat).all()

    return ChatTreeResponse(
        uuid=str(chat.uuid),
        owner_uuid=str(chat.owner_uuid),
        created=chat.created.isoformat(),
        updated=chat.updated.isoformat(),
        messages=[
            MessageResponse(
                uuid=str(msg.uuid),
                role=msg.role.value,
                content=msg.content,
                parent_uuid=str(msg.parent_id) if msg.parent_id else None,
                created_at=msg.created_at.isoformat(),
                updated_at=msg.updated_at.isoformat(),
            )
            for msg in messages
        ],
    )
