from uuid import UUID
from domain.entities.user_entity import UserEntity
from application.ports.output.user_repository import UserRepositoryProtocol
from infrastructure.db.models import UserModel


class UserRepositoryImpl(UserRepositoryProtocol):
    async def save(self, user: UserEntity) -> None:
        """ユーザーを保存（新規作成 or 更新）"""
        await UserModel.update_or_create(
            uuid=UUID(user.uuid),
            defaults={
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
            },
        )

    async def find_by_uuid(self, uuid: str) -> UserEntity | None:
        """UUIDでユーザーを取得"""
        try:
            user_model = await UserModel.get(uuid=UUID(uuid))
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active,
            )
        except Exception:
            return None

    async def find_by_email(self, email: str) -> UserEntity | None:
        """Emailでユーザーを取得"""
        try:
            user_model = await UserModel.get(email=email)
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active,
            )
        except Exception:
            return None

    async def find_by_username(self, username: str) -> UserEntity | None:
        """Usernameでユーザーを取得"""
        try:
            user_model = await UserModel.get(username=username)
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active,
            )
        except Exception:
            return None
