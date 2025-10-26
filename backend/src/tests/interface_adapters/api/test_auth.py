import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from src.infrastructure.db.models import UserModel
from src.infrastructure.security.password import PasswordHasher


@pytest_asyncio.fixture
async def test_user(init_db):
    """テスト用ユーザーを作成"""
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


@pytest.mark.asyncio
class TestAuthEndpoints:
    """認証エンドポイントのテスト"""

    async def test_login_success(self, test_user, client: TestClient):
        """正しい認証情報でログインできる"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, test_user, client: TestClient):
        """間違ったパスワードでログインは失敗する"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user(self, client: TestClient):
        """存在しないユーザーでログインは失敗する"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "some_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_inactive_user(self, test_user, client: TestClient):
        """非アクティブなユーザーでログインは失敗する"""
        user = test_user["user"]
        user.is_active = False
        await user.save()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": test_user["password"],
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_get_current_user_success(self, test_user, client: TestClient):
        """有効なトークンでユーザー情報を取得できる"""
        # まずログイン
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": test_user["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        # ユーザー情報を取得
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "uuid" in data
        assert "password_hash" not in data  # パスワードハッシュは返さない

    async def test_get_current_user_without_token(self, client: TestClient):
        """トークンなしではユーザー情報を取得できない"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # HTTPBearerは必須なので403が返る

    async def test_get_current_user_with_invalid_token(self, client: TestClient):
        """無効なトークンではユーザー情報を取得できない"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401
