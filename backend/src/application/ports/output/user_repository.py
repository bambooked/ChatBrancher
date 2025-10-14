from abc import ABC, abstractmethod

from domain.entities.user_entity import UserEntity


class UserRepositoryProtocol(ABC):
    """ユーザー情報の永続化を担当するリポジトリのインターフェース"""

    @abstractmethod
    async def save(self, user: UserEntity) -> None:
        """ユーザーを保存または更新"""
        pass

    @abstractmethod
    async def find_by_uuid(self, uuid: str) -> UserEntity | None:
        """UUIDでユーザーを検索"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> UserEntity | None:
        """メールアドレスでユーザーを検索"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> UserEntity | None:
        """ユーザー名でユーザーを検索"""
        pass
