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

# Tortoise ORMはpostgresql://スキームを認識しないため、postgres://に変換
# Renderなどのサービスはpostgresql://形式を提供することが多い
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgres://", 1)

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
