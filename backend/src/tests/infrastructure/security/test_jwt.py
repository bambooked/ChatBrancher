import pytest
from datetime import datetime, timedelta, timezone
from infrastructure.security.jwt import JWTHandler, InvalidTokenError


class TestJWTHandler:
    """JWTHandlerのテスト"""

    def test_create_access_token_with_default_expiration(self):
        """デフォルトの有効期限でアクセストークンを作成できる"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        token = handler.create_access_token(user_uuid=user_uuid)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """カスタム有効期限でアクセストークンを作成できる"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        expires_delta = timedelta(hours=1)
        token = handler.create_access_token(
            user_uuid=user_uuid, expires_delta=expires_delta
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self):
        """有効なトークンを検証できる"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        token = handler.create_access_token(user_uuid=user_uuid)

        decoded_user_uuid = handler.verify_token(token)
        assert decoded_user_uuid == user_uuid

    def test_verify_token_with_expired_token(self):
        """期限切れトークンの検証は失敗する"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        expires_delta = timedelta(seconds=-1)  # すでに期限切れ
        token = handler.create_access_token(
            user_uuid=user_uuid, expires_delta=expires_delta
        )

        with pytest.raises(InvalidTokenError) as exc_info:
            handler.verify_token(token)
        assert "expired" in str(exc_info.value).lower()

    def test_verify_token_with_invalid_signature(self):
        """不正な署名のトークンの検証は失敗する"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        token = handler.create_access_token(user_uuid=user_uuid)

        # 異なるシークレットキーで検証を試みる
        wrong_handler = JWTHandler(secret_key="wrong-secret-key", algorithm=algorithm)

        with pytest.raises(InvalidTokenError) as exc_info:
            wrong_handler.verify_token(token)
        assert "invalid" in str(exc_info.value).lower() or "signature" in str(
            exc_info.value
        ).lower()

    def test_verify_token_with_malformed_token(self):
        """形式が不正なトークンの検証は失敗する"""
        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        malformed_token = "this.is.not.a.valid.jwt"

        with pytest.raises(InvalidTokenError):
            handler.verify_token(malformed_token)

    def test_verify_token_with_missing_sub_claim(self):
        """subクレームが欠けているトークンの検証は失敗する"""
        from jose import jwt

        secret_key = "test-secret-key"
        algorithm = "HS256"
        handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)

        # subクレームなしでトークンを手動で作成
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {"exp": expire}
        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        with pytest.raises(InvalidTokenError) as exc_info:
            handler.verify_token(token)
        assert "invalid" in str(exc_info.value).lower()
