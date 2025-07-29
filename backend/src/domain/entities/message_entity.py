from dataclasses import dataclass
from enum import Enum
import uuid


class Role(str, Enum):
    """
    メッセージの送信者役割を表す列挙型
    Values:
        USER: ユーザーからのメッセージ（質問、指示等）
        ASSISTANT: AIアシスタントからの応答メッセージ
        SYSTEM: システムからの制御メッセージ（プロンプト、設定等）
    """

    USER = "user"  # ユーザーメッセージ：会話の開始、質問、指示
    ASSISTANT = "assistant"  # アシスタントメッセージ：AIからの応答、回答
    SYSTEM = "system"  # システムメッセージ：プロンプト、動作指示、設定


@dataclass
class MessageEntity:
    """
    チャット内の個別メッセージを表現するドメインエンティティ

    Attributes:
        id (int): データベース内での一意識別子
        uuid (str): グローバル一意識別子（UUID形式）
        role (Role): メッセージの送信者役割
        content (str): メッセージの実際の内容テキスト
    """

    uuid: str
    role: Role
    content: str

    @classmethod
    def create_user_message(cls, content: str) -> "MessageEntity":
        """ユーザーメッセージの作成"""
        return cls(
            uuid=str(uuid.uuid4()),
            role=Role.USER,
            content=content,
        )

    @classmethod
    def create_assistant_message(cls, content: str) -> "MessageEntity":
        """アシスタントメッセージの作成"""
        return cls(
            uuid=str(uuid.uuid4()),
            role=Role.ASSISTANT,
            content=content,
        )
    
    @classmethod
    def create_system_message(cls, content: str) -> "MessageEntity":
        """システムメッセージの作成"""
        return cls(
            uuid=str(uuid.uuid4()),
            role=Role.SYSTEM,
            content=content,
        )
