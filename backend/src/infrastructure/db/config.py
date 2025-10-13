"""
TortoiseORM設定

このモジュールはTortoiseORMとAerichマイグレーションツールの設定を提供します。
"""
from pathlib import Path

# backend/db.sqlite3 への絶対パスを生成
# config.py は backend/src/infrastructure/db/ にあるので、3階層上がbackend/
DB_PATH = Path(__file__).parent.parent.parent.parent / "db.sqlite3"

TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{DB_PATH}"
    },
    "apps": {
        "models": {
            "models": ["infrastructure.db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
