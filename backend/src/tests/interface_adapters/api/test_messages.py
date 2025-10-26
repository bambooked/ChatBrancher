import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from src.infrastructure.db.models import UserModel, ChatTreeDetail, MessageModel
from src.infrastructure.security.password import PasswordHasher
from src.domain.entities.message_entity import Role
from src.infrastructure.config import settings


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
        user_context_id=authenticated_user["user"].uuid,
    )

    yield {"chat": chat, "root_message": root_message, "user": authenticated_user["user"]}

    # クリーンアップ
    await MessageModel.filter(chat_tree=chat).delete()
    await chat.delete()


@pytest.mark.asyncio
class TestMessageEndpoints:
    """メッセージ送信エンドポイントのテスト"""

    @pytest.mark.skipif(
        not settings.OPENROUTER_API_KEY,
        reason="OPENROUTER_API_KEY not set"
    )
    async def test_send_message_success(
        self, test_chat, auth_headers, client: TestClient
    ):
        """メッセージを送信してLLMレスポンスを取得できる"""
        chat_uuid = str(test_chat["chat"].uuid)
        parent_uuid = str(test_chat["root_message"].uuid)

        response = client.post(
            f"/api/v1/chats/{chat_uuid}/messages",
            headers=auth_headers,
            json={
                "content": "Say 'test successful' and nothing else",
                "parent_message_uuid": parent_uuid
            },
        )

        if response.status_code != 200:
            print(f"DEBUG: Status={response.status_code}, Body={response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "user_message" in data
        assert "assistant_message" in data
        assert data["user_message"]["content"] == "Say 'test successful' and nothing else"
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["assistant_message"]["content"]) > 0

    async def test_send_message_to_nonexistent_chat(
        self, auth_headers, client: TestClient
    ):
        """存在しないチャットにメッセージを送信できない"""
        nonexistent_uuid = str(uuid4())
        response = client.post(
            f"/api/v1/chats/{nonexistent_uuid}/messages",
            headers=auth_headers,
            json={"content": "Test message", "parent_message_uuid": None},
        )

        assert response.status_code == 404

    async def test_send_message_to_other_user_chat(
        self, test_chat, client: TestClient
    ):
        """他のユーザーのチャットにメッセージを送信できない"""
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

        chat_uuid = str(test_chat["chat"].uuid)
        response = client.post(
            f"/api/v1/chats/{chat_uuid}/messages",
            headers=other_headers,
            json={"content": "Test message", "parent_message_uuid": None},
        )

        assert response.status_code == 403

        # クリーンアップ
        await other_user.delete()

    async def test_send_message_without_auth(self, test_chat, client: TestClient):
        """認証なしではメッセージを送信できない"""
        chat_uuid = str(test_chat["chat"].uuid)
        response = client.post(
            f"/api/v1/chats/{chat_uuid}/messages",
            json={"content": "Test message", "parent_message_uuid": None},
        )

        assert response.status_code == 403

    async def test_send_message_with_nonexistent_parent(
        self, test_chat, auth_headers, client: TestClient
    ):
        """存在しない親メッセージを指定できない"""
        chat_uuid = str(test_chat["chat"].uuid)
        nonexistent_parent_uuid = str(uuid4())

        response = client.post(
            f"/api/v1/chats/{chat_uuid}/messages",
            headers=auth_headers,
            json={
                "content": "Test message",
                "parent_message_uuid": nonexistent_parent_uuid,
            },
        )

        # 親メッセージが存在しない場合は404が返る
        assert response.status_code == 404
