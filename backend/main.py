import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from src.interface_adapters.api.auth import router as auth_router
from src.interface_adapters.api.chats import router as chats_router
from src.interface_adapters.api.messages import router as messages_router
from src.infrastructure.db.config import TORTOISE_ORM

app = FastAPI(title="ChatBrancher API", version="0.1.0")

# CORS設定（開発環境用）
# 本番環境では静的ファイル配信のため不要だが、開発時は必要
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
if CORS_ORIGINS and CORS_ORIGINS[0]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 環境変数が設定されていない場合はデフォルトの開発用設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーターを登録（個々のルーターでプレフィックスを定義）
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(messages_router)


@app.get("/api/health")
async def health_check():
    """ヘルスチェックエンドポイント（render.com等で使用）"""
    return {"status": "healthy"}


@app.get("/api")
async def api_root():
    """APIルートエンドポイント"""
    return {"message": "ChatBrancher API", "version": "0.1.0"}


# 静的ファイル配信（本番環境用）
# フロントエンドのビルド成果物が存在する場合のみマウント
FRONTEND_BUILD_DIR = Path(__file__).parent / "frontend" / "build"
if FRONTEND_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="static")

# テスト環境ではregister_tortoiseをスキップ（conftest.pyで手動初期化）
if os.getenv("TESTING") != "1":
    # Tortoise ORMをFastAPIに統合
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
