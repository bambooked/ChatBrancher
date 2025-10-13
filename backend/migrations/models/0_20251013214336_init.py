from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "chat_tree_detail" (
    "uuid" CHAR(36) NOT NULL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* チャットの詳細を保持する */;
CREATE TABLE IF NOT EXISTS "messages" (
    "uuid" CHAR(36) NOT NULL PRIMARY KEY,
    "role" VARCHAR(9) NOT NULL /* USER: user\nASSISTANT: assistant\nSYSTEM: system */,
    "content" TEXT NOT NULL,
    "user_context_id" CHAR(36),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "chat_tree_id" CHAR(36) NOT NULL REFERENCES "chat_tree_detail" ("uuid") ON DELETE CASCADE,
    "parent_id" CHAR(36) REFERENCES "messages" ("uuid") ON DELETE SET NULL
) /* メッセージのTortoiseモデル（シンプル版：メモリ上で木構造操作） */;
CREATE TABLE IF NOT EXISTS "assistant_message_details" (
    "provider" VARCHAR(100),
    "model_name" VARCHAR(100),
    "prompt_tokens" INT NOT NULL DEFAULT 0,
    "completion_tokens" INT NOT NULL DEFAULT 0,
    "total_tokens" INT NOT NULL DEFAULT 0,
    "temperature" REAL,
    "max_tokens" INT,
    "finish_reason" VARCHAR(50),
    "gen_id" VARCHAR(255),
    "object_" VARCHAR(50),
    "created_timestamp" VARCHAR(50),
    "message_id" CHAR(36) NOT NULL PRIMARY KEY REFERENCES "messages" ("uuid") ON DELETE CASCADE
) /* アシスタントメッセージの詳細情報（LLM関連データ） */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "hz24+mblsavP4f5dTKxw=="
)
