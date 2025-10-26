import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from src.interface_adapters.api.auth import router as auth_router
from src.interface_adapters.api.chats import router as chats_router
from src.interface_adapters.api.messages import router as messages_router
from src.infrastructure.db.config import TORTOISE_ORM

app = FastAPI(title="ChatBrancher API", version="0.1.0")

# CORS設定
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

# ルーターを登録
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(messages_router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "ChatBrancher API"}


# テスト環境ではregister_tortoiseをスキップ（conftest.pyで手動初期化）
if os.getenv("TESTING") != "1":
    # Tortoise ORMをFastAPIに統合
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
