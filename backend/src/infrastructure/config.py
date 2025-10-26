import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定"""

    # JWT設定
    SECRET_KEY= os.getenv("SECRET_KEY", "my_secret_keyyyyyyyyyy")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # LLM API設定
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")


settings = Settings()
