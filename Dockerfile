# ========================================
# Stage 1: フロントエンドのビルド
# ========================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# 依存関係のインストール
COPY frontend/package*.json ./
RUN npm ci

# ビルド
COPY frontend/ ./
RUN npm run build

# ========================================
# Stage 2: バックエンド + 静的ファイル配信
# ========================================
FROM python:3.13-slim

WORKDIR /app

# uvのインストール
RUN pip install --no-cache-dir uv

# バックエンドの依存関係をインストール
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --no-dev

# バックエンドのソースコードをコピー
COPY backend/ ./

# フロントエンドのビルド成果物をコピー
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# ポート公開
EXPOSE 8000

# 本番環境で起動
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
