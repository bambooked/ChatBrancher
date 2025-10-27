"""
TortoiseORM設定

このモジュールはTortoiseORMとAerichマイグレーションツールの設定を提供します。
"""
import os

# 環境変数からDATABASE_URLを取得（必須）
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it in your .env file or environment."
    )

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["src.infrastructure.db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
