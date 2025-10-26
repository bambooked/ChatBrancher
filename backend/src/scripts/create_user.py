import asyncio
import sys
import getpass
from uuid import uuid4
from tortoise import Tortoise
from src.infrastructure.db.config import TORTOISE_ORM
from src.infrastructure.db.models import UserModel
from src.infrastructure.security.password import PasswordHasher


async def init_db():
    """DBを初期化"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def create_user(username: str, email: str, password: str) -> str:
    """新規ユーザーを作成"""
    await init_db()

    # 重複チェック
    existing_username = await UserModel.filter(username=username).first()
    if existing_username:
        raise ValueError(f"Username '{username}' already exists")

    existing_email = await UserModel.filter(email=email).first()
    if existing_email:
        raise ValueError(f"Email '{email}' already exists")

    # パスワードをハッシュ化
    password_hash = PasswordHasher.hash_password(password)

    # ユーザー作成
    user_uuid = uuid4()
    await UserModel.create(
        uuid=user_uuid,
        username=username,
        email=email,
        password_hash=password_hash,
        is_active=True,
    )

    return str(user_uuid)


async def list_users():
    """登録済みユーザー一覧を表示"""
    await init_db()
    users = await UserModel.all()

    if not users:
        print("No users found.")
        return

    print("\n=== Registered Users ===")
    for user in users:
        status = "Active" if user.is_active else "Inactive"
        print(f"UUID: {user.uuid}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Status: {status}")
        print(f"  Created: {user.created_at}")
        print()


async def main():
    try:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  Create user: uv run python -m scripts.create_user create <username> <email>")
            print("  List users:  uv run python -m scripts.create_user list")
            sys.exit(1)

        command = sys.argv[1]

        if command == "create":
            if len(sys.argv) != 4:
                print("Error: create command requires <username> and <email>")
                sys.exit(1)

            username = sys.argv[2]
            email = sys.argv[3]

            # パスワード入力（非表示）
            password = getpass.getpass("Enter password: ")
            password_confirm = getpass.getpass("Confirm password: ")

            if password != password_confirm:
                print("\n❌ Error: Passwords do not match")
                sys.exit(1)

            if len(password) < 8:
                print("\n❌ Error: Password must be at least 8 characters")
                sys.exit(1)

            try:
                user_uuid = await create_user(username, email, password)
                print("\n✅ User created successfully!")
                print(f"UUID: {user_uuid}")
                print(f"Username: {username}")
                print(f"Email: {email}")
                print("\n📋 Please provide the username and password to the user for login.")
            except ValueError as e:
                print(f"\n❌ Error: {e}")
                sys.exit(1)

        elif command == "list":
            await list_users()

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    finally:
        # DB接続が初期化されている場合のみクローズ
        if Tortoise._inited:
            await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
