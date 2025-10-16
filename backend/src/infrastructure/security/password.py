import bcrypt


class PasswordHasher:
    """パスワードのハッシュ化と検証を行うユーティリティ"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        パスワードをbcryptでハッシュ化

        Args:
            password: プレーンテキストのパスワード

        Returns:
            ハッシュ化されたパスワード（文字列）
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        パスワードとハッシュが一致するか検証

        Args:
            password: プレーンテキストのパスワード
            password_hash: ハッシュ化されたパスワード

        Returns:
            一致する場合True、それ以外False
        """
        password_bytes = password.encode("utf-8")
        password_hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, password_hash_bytes)
