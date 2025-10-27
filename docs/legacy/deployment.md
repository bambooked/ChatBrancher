# デプロイ準備ガイド

## 概要

このドキュメントは、ChatBrancherをrender.comにデプロイするための準備作業をまとめたものです。

## 実施した変更

### 1. PostgreSQL対応

**意図**: 本番環境でのデータベースをPostgreSQLに統一

**変更内容**:
- `backend/pyproject.toml`: `asyncpg>=0.30.0`を追加
- `backend/src/infrastructure/db/config.py`: `DATABASE_URL`環境変数からDB接続先を読み込むように変更
- SQLiteファイルを削除（本番環境ではPostgreSQL必須）

**使い方**:
- 環境変数`DATABASE_URL`にPostgreSQL接続文字列を設定
- 例: `postgres://user:password@host:5432/database`

---

### 2. Docker環境の整備

#### 2.1 開発環境（docker-compose.yml）

**意図**: ローカル開発環境を本番環境に近い構成で再現

**構成**:
```
- postgres: PostgreSQLコンテナ（5432ポート）
- backend: FastAPI開発サーバー（8000ポート、ホットリロード有効）
- frontend: Vite開発サーバー（5173ポート、HMR有効）
```

**使い方**:
```bash
# 環境変数ファイルを準備
cp backend/.env.example backend/.env
# DATABASE_URL等を編集

# 起動
docker-compose up --build

# 停止
docker-compose down

# データも削除する場合
docker-compose down -v
```

**補足**:
- `backend/Dockerfile.dev`: バックエンド開発用Dockerfile（uvicorn --reload）
- `frontend/Dockerfile.dev`: フロントエンド開発用Dockerfile（npm run dev）

#### 2.2 本番環境（Dockerfile）

**意図**: render.comで動作する単一コンテナを構築

**構成**:
- **Stage 1**: フロントエンドをビルド → 静的ファイル生成（HTML/CSS/JS）
- **Stage 2**: バックエンド + 静的ファイルを配信

**動作**:
- FastAPIが`/api/*`でAPIを提供
- FastAPIが`/*`で静的ファイル（SvelteKitビルド成果物）を配信
- 1つのコンテナで完結（CORSの設定不要）

**使い方**:
```bash
# ビルド
docker build -t chatbrancher:latest .

# ローカルでテスト実行
docker run -p 8000:8000 \
  -e DATABASE_URL="postgres://..." \
  -e SECRET_KEY="..." \
  -e OPENROUTER_API_KEY="..." \
  chatbrancher:latest

# ブラウザで http://localhost:8000 にアクセス
```

**render.comでの使い方**:
1. Web Serviceを作成
2. Environment: Docker
3. Dockerfileを指定（ルートの`Dockerfile`）
4. 環境変数を設定（次のセクション参照）

---

### 3. 環境変数

#### 3.1 バックエンド（backend/.env.example）

**意図**: 環境ごとに設定を切り替え可能に

**必須の環境変数**:
```bash
# データベース接続
DATABASE_URL=postgres://user:password@host:5432/database

# JWT認証
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API
OPENROUTER_API_KEY=your-openrouter-api-key-here

# テストモード（本番では不要）
TESTING=0
```

**オプション**:
```bash
# CORS設定（docker-compose開発環境用）
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
# 本番環境では不要（静的配信のため）
```

#### 3.2 フロントエンド（frontend/.env.example）

**意図**: 開発環境と本番環境でAPI URLを切り替え

**設定**:
```bash
# 開発環境: バックエンドのURL
VITE_API_URL=http://localhost:8000

# 本番環境: 空文字列（同一オリジン）
# VITE_API_URL=
```

**仕組み**:
- `frontend/src/lib/config.ts`: `VITE_API_URL`を読み込み
- 空文字列の場合は相対パス（`/api/*`）でアクセス
- 開発環境では`http://localhost:8000/api/*`でアクセス

---

### 4. アプリケーションの変更

#### 4.1 backend/main.py

**変更内容**:
1. **APIプレフィックス追加**: `/api/*`でAPIを提供
   - `/api/auth/login`
   - `/api/chats`
   - `/api/chats/{uuid}/messages`

2. **ヘルスチェック**: `/api/health` エンドポイント追加（render.com用）

3. **静的ファイル配信**: `frontend/build/`が存在する場合、`/*`で配信

4. **CORS設定**: 環境変数`CORS_ORIGINS`で制御（開発環境用）

#### 4.2 フロントエンド

**変更内容**:
1. **API設定の一元化**:
   - `frontend/src/lib/config.ts`: 環境変数から`API_BASE_URL`を取得
   - `frontend/src/lib/api/index.ts`: シングルトンAPIクライアント提供

2. **各ページの修正**: ハードコードされた`http://localhost:8000`を削除
   - `routes/login/+page.svelte`
   - `routes/chats/+page.svelte`
   - `routes/chats/[chatId]/+page.svelte`

---

## マイグレーション実行（render.com）

**手順**:
1. render.comのShellにアクセス
2. マイグレーション実行:
   ```bash
   uv run aerich upgrade
   ```

**初回セットアップ**（マイグレーションファイルが未生成の場合）:
```bash
# ローカルで実行
cd backend
PYTHONPATH=src uv run aerich init -t src.infrastructure.db.config.TORTOISE_ORM
PYTHONPATH=src uv run aerich init-db
# 生成されたmigrationsフォルダをgit commit
```

---

## デプロイフロー

### 開発フロー
```
1. コード編集
2. docker-compose up（ホットリロード）
3. 動作確認
4. git commit & push
```

### デプロイフロー
```
1. git push
2. render.comが自動ビルド（Dockerfile）
3. render.comでマイグレーション実行（手動）
4. デプロイ完了
```

---

## トラブルシューティング

### 開発環境でPostgreSQLに接続できない
- `docker-compose up`でpostgresコンテナが起動しているか確認
- `backend/.env`の`DATABASE_URL`が正しいか確認
  - ホスト名は`postgres`（コンテナ名）

### フロントエンドがAPIにアクセスできない
- 開発環境: `frontend/.env`に`VITE_API_URL=http://localhost:8000`を設定
- 本番環境: 環境変数を設定せず（空文字列）

### 本番環境でフロントエンドが表示されない
- Dockerビルドが成功しているか確認
- `frontend/build/`ディレクトリが生成されているか確認（ビルドログ確認）
- `backend/main.py`の静的ファイルマウントロジックを確認

---

## ファイル一覧

### 新規作成
- `Dockerfile`: 本番用（マルチステージビルド）
- `docker-compose.yml`: 開発環境用
- `.dockerignore`: Docker効率化
- `backend/Dockerfile.dev`: 開発用
- `backend/.dockerignore`
- `backend/.env.example`: 環境変数テンプレート
- `frontend/Dockerfile.dev`: 開発用
- `frontend/.dockerignore`
- `frontend/.env.example`: 環境変数テンプレート
- `frontend/src/lib/config.ts`: API URL設定
- `frontend/src/lib/api/index.ts`: APIクライアント
- `frontend/src/routes/+layout.js`: SPAモード設定（prerender無効化）

### 変更
- `backend/pyproject.toml`: asyncpg追加
- `backend/src/infrastructure/db/config.py`: 環境変数対応（PostgreSQL必須）
- `backend/main.py`: API prefix, 静的配信, ヘルスチェック
- `frontend/package.json`: @sveltejs/adapter-static追加
- `frontend/svelte.config.js`: adapter-staticに変更（静的ビルド）
- `frontend/src/routes/login/+page.svelte`: API URL修正
- `frontend/src/routes/chats/+page.svelte`: API URL修正
- `frontend/src/routes/chats/[chatId]/+page.svelte`: API URL修正
