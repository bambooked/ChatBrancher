from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "chat_tree_detail" (
    "uuid" UUID NOT NULL PRIMARY KEY,
    "owner_uuid" UUID NOT NULL,
    "created" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "chat_tree_detail" IS 'チャットの詳細を保持する';
CREATE TABLE IF NOT EXISTS "messages" (
    "uuid" UUID NOT NULL PRIMARY KEY,
    "role" VARCHAR(9) NOT NULL,
    "content" TEXT NOT NULL,
    "user_context_id" UUID,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "chat_tree_id" UUID NOT NULL REFERENCES "chat_tree_detail" ("uuid") ON DELETE CASCADE,
    "parent_id" UUID REFERENCES "messages" ("uuid") ON DELETE SET NULL
);
COMMENT ON COLUMN "messages"."role" IS 'USER: user\nASSISTANT: assistant\nSYSTEM: system';
COMMENT ON TABLE "messages" IS 'メッセージのTortoiseモデル（シンプル版：メモリ上で木構造操作）';
CREATE TABLE IF NOT EXISTS "assistant_message_details" (
    "provider" VARCHAR(100),
    "model_name" VARCHAR(100),
    "prompt_tokens" INT NOT NULL DEFAULT 0,
    "completion_tokens" INT NOT NULL DEFAULT 0,
    "total_tokens" INT NOT NULL DEFAULT 0,
    "temperature" DOUBLE PRECISION,
    "max_tokens" INT,
    "finish_reason" VARCHAR(50),
    "gen_id" VARCHAR(255),
    "object_" VARCHAR(50),
    "created_timestamp" VARCHAR(50),
    "message_id" UUID NOT NULL PRIMARY KEY REFERENCES "messages" ("uuid") ON DELETE CASCADE
);
COMMENT ON TABLE "assistant_message_details" IS 'アシスタントメッセージの詳細情報（LLM関連データ）';
CREATE TABLE IF NOT EXISTS "users" (
    "uuid" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "users" IS 'ユーザー情報を保持する';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "QRF2vb0uWSxBFqwRTHB+6CcIh5qXh38ADIFnrA=="
)
