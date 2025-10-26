import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from src.infrastructure.db.models import UserModel, ChatTreeDetail, MessageModel
from src.infrastructure.security.password import PasswordHasher
from src.domain.entities.message_entity import Role


@pytest_asyncio.fixture
async def authenticated_user(init_db):
    """認証済みテストユーザーを作成"""
    user_uuid = uuid4()
    password = "test_password_123"
    password_hash = PasswordHasher.hash_password(password)

    user = await UserModel.create(
        uuid=user_uuid,
        username="testuser",
        email="test@example.com",
        password_hash=password_hash,
        is_active=True,
    )

    yield {"user": user, "password": password}

    # クリーンアップ
    await user.delete()


@pytest_asyncio.fixture
async def auth_headers(authenticated_user, client: TestClient):
    """認証ヘッダーを取得"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": authenticated_user["user"].username,
            "password": authenticated_user["password"],
        },
    )
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def test_chat(authenticated_user):
    """テスト用チャットを作成"""
    chat_uuid = uuid4()
    chat = await ChatTreeDetail.create(
        uuid=chat_uuid, owner_uuid=authenticated_user["user"].uuid
    )

    # ルートメッセージを作成
    root_message = await MessageModel.create(
        uuid=uuid4(),
        role=Role.USER,
        content="Hello",
        parent=None,
        chat_tree=chat,
    )

    yield {"chat": chat, "root_message": root_message}

    # クリーンアップ
    await MessageModel.filter(chat_tree=chat).delete()
    await chat.delete()


@pytest.mark.asyncio
class TestChatEndpoints:
    """チャット管理エンドポイントのテスト"""

    async def test_create_chat_success(self, auth_headers, client: TestClient):
        """新しいチャットを作成できる"""
        response = client.post("/api/v1/chats", headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "uuid" in data
        assert "owner_uuid" in data
        assert "created" in data
        assert "updated" in data

    async def test_create_chat_without_auth(self, client: TestClient):
        """認証なしではチャットを作成できない"""
        response = client.post("/api/v1/chats")

        assert response.status_code == 403

    async def test_get_all_chats_success(
        self, authenticated_user, auth_headers, test_chat, client: TestClient
    ):
        """ユーザーの全チャット一覧を取得できる"""
        response = client.get("/api/v1/chats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(chat["uuid"] == str(test_chat["chat"].uuid) for chat in data)

    async def test_get_all_chats_empty(self, auth_headers, client: TestClient):
        """チャットがない場合は空リストを返す"""
        response = client.get("/api/v1/chats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_all_chats_without_auth(self, client: TestClient):
        """認証なしではチャット一覧を取得できない"""
        response = client.get("/api/v1/chats")

        assert response.status_code == 403

    async def test_get_chat_tree_success(
        self, authenticated_user, auth_headers, test_chat, client: TestClient
    ):
        """特定のチャットツリーを取得できる"""
        chat_uuid = str(test_chat["chat"].uuid)
        response = client.get(f"/api/v1/chats/{chat_uuid}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "uuid" in data
        assert data["uuid"] == chat_uuid
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 1

    async def test_get_chat_tree_nonexistent(self, auth_headers, client: TestClient):
        """存在しないチャットは取得できない"""
        nonexistent_uuid = str(uuid4())
        response = client.get(f"/api/v1/chats/{nonexistent_uuid}", headers=auth_headers)

        assert response.status_code == 404

    async def test_get_chat_tree_other_user(
        self, authenticated_user, test_chat, client: TestClient
    ):
        """他のユーザーのチャットは取得できない"""
        # 別のユーザーを作成
        other_user = await UserModel.create(
            uuid=uuid4(),
            username="otheruser",
            email="other@example.com",
            password_hash=PasswordHasher.hash_password("password"),
            is_active=True,
        )

        # 別のユーザーでログイン
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "otheruser", "password": "password"},
        )
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # test_chatにアクセスを試みる
        chat_uuid = str(test_chat["chat"].uuid)
        response = client.get(f"/api/v1/chats/{chat_uuid}", headers=other_headers)

        assert response.status_code == 403

        # クリーンアップ
        await other_user.delete()

    async def test_get_chat_tree_without_auth(self, test_chat, client: TestClient):
        """認証なしではチャットツリーを取得できない"""
        chat_uuid = str(test_chat["chat"].uuid)
        response = client.get(f"/api/v1/chats/{chat_uuid}")

        assert response.status_code == 403
