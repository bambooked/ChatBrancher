"""チャットアクセス権限検証ユースケース"""

from domain.entities.user_entity import UserEntity
from domain.entities.chat_tree_entity import ChatTreeEntity


class AccessDeniedError(Exception):
    """アクセス拒否エラー"""
    pass


class VerifyChatAccess:
    """チャットへのアクセス権限を検証するユースケース"""

    def verify(self, user: UserEntity, chat_tree: ChatTreeEntity) -> None:
        """
        ユーザーが指定されたチャットにアクセスできるかを検証

        Args:
            user: アクセスを試みるユーザー
            chat_tree: アクセス対象のチャットツリー

        Raises:
            AccessDeniedError: アクセスが拒否された場合
        """
        # ユーザーが無効化されている場合
        if not user.is_active:
            raise AccessDeniedError(f"User {user.uuid} is inactive")

        # ユーザーがチャットの所有者でない場合
        if not chat_tree.is_owned_by(user.uuid):
            raise AccessDeniedError(
                f"User {user.uuid} does not have access to chat {chat_tree.uuid}: access denied"
            )
