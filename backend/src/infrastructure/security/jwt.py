from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt


class InvalidTokenError(Exception):
    """トークンが無効な場合の例外"""

    pass


class JWTHandler:
    """JWT トークンの生成と検証を行うハンドラー"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Args:
            secret_key: JWT署名用のシークレットキー
            algorithm: 使用するアルゴリズム（デフォルト: HS256）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self, user_uuid: str, expires_delta: timedelta | None = None
    ) -> str:
        """
        アクセストークンを生成

        Args:
            user_uuid: ユーザーのUUID
            expires_delta: 有効期限（Noneの場合は15分）

        Returns:
            JWTトークン文字列
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)

        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": user_uuid, "exp": expire}

        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> str:
        """
        トークンを検証してユーザーUUIDを取得

        Args:
            token: 検証するJWTトークン

        Returns:
            ユーザーUUID

        Raises:
            InvalidTokenError: トークンが無効な場合
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_uuid: str | None = payload.get("sub")

            if user_uuid is None:
                raise InvalidTokenError("Invalid token: missing subject")

            return user_uuid

        except JWTError as e:
            # 期限切れや署名不正などのエラーを統一的に処理
            raise InvalidTokenError(f"Invalid token: {str(e)}") from e
