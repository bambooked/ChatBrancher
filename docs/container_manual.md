# Docker開発環境マニュアル

## 概要

このプロジェクトはDocker Composeを使用した開発環境に移行しました。
このドキュメントでは、従来の開発フローからの変更点と、新しい操作方法を説明します。

---

## なぜDockerを使うのか？

### 1. データベースの統一
- SQLiteは本番環境で使えない（並行処理に弱い）
- 開発環境と本番環境で同じPostgreSQLを使うことで、本番特有のバグを減らせる

### 2. 環境の再現性
- 「自分のマシンでは動く」問題を防ぐ
- チームメンバー全員が同じ環境で開発できる

### 3. デプロイとの一貫性
- render.comではDockerコンテナでデプロイ
- 開発時も同じDockerを使うことで、デプロイ前に問題を発見できる

### 4. セットアップの簡略化
- 新しいメンバーが参加する場合、`docker-compose up`だけで環境構築完了
- PostgreSQLのインストールや設定が不要

---

## 開発環境の構成

```
┌─────────────────────────────────┐
│  docker-compose                 │
│  ┌───────────────────────────┐  │
│  │ PostgreSQL (port 5432)    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Backend (port 8000)       │  │
│  │ - FastAPI                 │  │
│  │ - ホットリロード有効       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Frontend (port 5173)      │  │
│  │ - Vite dev server         │  │
│  │ - HMR有効                 │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

---

## 操作方法の変更まとめ

### 1. 環境の起動・停止

#### 従来
```bash
# バックエンド（別ターミナル）
cd backend
uv run uvicorn main:app --reload

# フロントエンド（別ターミナル）
cd frontend
npm run dev
```

#### 現在
```bash
# プロジェクトルートで全て起動
docker-compose up

# バックグラウンドで起動
docker-compose up -d

# 停止
docker-compose down

# データベースも含めて完全削除
docker-compose down -v
```

---

### 2. 依存関係のインストール

#### 従来
```bash
# バックエンド
cd backend
uv sync

# フロントエンド
cd frontend
npm install
```

#### 現在

**パターンA: コンテナを再ビルド（推奨）**
```bash
docker-compose up --build
```

**パターンB: ローカルでもインストール（エディタの補完用）**
```bash
# バックエンド（エディタの補完のため）
cd backend
uv sync

# フロントエンド（エディタの補完のため）
cd frontend
npm install

# コンテナは再ビルド
docker-compose up --build
```

**補足**: ホットリロードが有効なので、コード変更は即座に反映されます。

---

### 3. データベース関連

#### 従来（SQLite）
```bash
# データベースファイルがそのままある
# backend/db.sqlite3

# マイグレーション
cd backend
PYTHONPATH=src uv run aerich upgrade
```

#### 現在（PostgreSQL in Docker）
```bash
# マイグレーション実行
docker-compose exec backend uv run aerich upgrade

# 新しいマイグレーション作成
docker-compose exec backend uv run aerich migrate --name add_new_field

# データベースの初期化（最初の一回のみ）
docker-compose exec backend uv run aerich init-db
```

**重要**: `docker-compose exec backend <コマンド>` でバックエンドコンテナ内のコマンドを実行します。

---

### 4. テストの実行

#### 従来
```bash
cd backend
PYTHONPATH=src uv run pytest
```

#### 現在
```bash
# バックエンドのテスト（コンテナ内）
docker-compose exec backend uv run pytest

# または、ローカルで実行（テスト用DB設定が必要）
cd backend
PYTHONPATH=src TESTING=1 uv run pytest
```

---

### 5. ログの確認

#### 新しい操作
```bash
# 全サービスのログ
docker-compose logs

# 特定サービスのログ
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# リアルタイムでログを追跡
docker-compose logs -f backend

# 最新N行のみ表示
docker-compose logs --tail=50 backend
```

---

### 6. コンテナ内でシェルを開く

#### 新しい操作
```bash
# バックエンドコンテナ内でシェル起動
docker-compose exec backend /bin/bash

# フロントエンドコンテナ内でシェル起動
docker-compose exec frontend /bin/bash

# コンテナ内で任意のコマンドを実行
docker-compose exec backend ls -la
docker-compose exec backend uv run python -c "print('hello')"
```

---

### 7. コードの編集

#### 変更なし！
```bash
# エディタでファイルを編集
# 保存すると自動リロード（ボリュームマウントのおかげ）
```

**理由**: `docker-compose.yml`でボリュームマウント設定済みなので、ローカルの`backend/`や`frontend/`ディレクトリの変更がリアルタイムで反映されます。

---

### 8. データベースのリセット

#### 従来（SQLite）
```bash
# ファイル削除
rm backend/db.sqlite3

# マイグレーション再実行
PYTHONPATH=src uv run aerich upgrade
```

#### 現在（PostgreSQL）
```bash
# データベースを含めて完全削除
docker-compose down -v

# 再起動（DBも新規作成される）
docker-compose up -d

# マイグレーション実行
docker-compose exec backend uv run aerich upgrade
```

---

### 9. 環境変数の変更

#### 操作方法
```bash
# backend/.env または frontend/.env を編集

# コンテナ再起動
docker-compose restart backend

# または完全に再起動
docker-compose down
docker-compose up -d
```

---

### 10. コンテナとポートの確認

```bash
# 起動中のコンテナとポートを確認
docker-compose ps

# 期待される出力:
# chatbrancher-postgres  -> 5432:5432
# chatbrancher-backend   -> 8000:8000
# chatbrancher-frontend  -> 5173:5173
```

---

## 日常的な開発フロー

### 開発開始
```bash
# 1. 朝イチで起動
docker-compose up -d

# 2. ログを確認（必要なら）
docker-compose logs -f backend

# 3. コードを編集（VSCodeなど）
#    → 自動でリロードされる

# 4. ブラウザでアクセス
#    - フロントエンド: http://localhost:5173
#    - バックエンドAPI: http://localhost:8000/api
```

### 開発終了
```bash
# コンテナ停止
docker-compose down

# データを残したい場合は -v を付けない
```

---

## 特殊なケース

### 新しい依存関係を追加した場合

```bash
# 1. package.json や pyproject.toml を編集

# 2. コンテナを再ビルド
docker-compose up --build

# または、個別にビルド
docker-compose build backend
docker-compose up -d
```

### マイグレーションを追加した場合

```bash
# 1. モデルを編集（backend/src/infrastructure/db/models.py）

# 2. マイグレーションファイル生成
docker-compose exec backend uv run aerich migrate --name add_new_field

# 3. マイグレーション実行
docker-compose exec backend uv run aerich upgrade

# 4. Git commitして共有
git add backend/migrations/
git commit -m "Add migration for new field"
```

### データベースをリセットしたい場合

```bash
# すべてクリーンアップ
docker-compose down -v

# 再起動
docker-compose up -d

# マイグレーション実行
docker-compose exec backend uv run aerich init-db
```

### 特定のコンテナだけ再起動

```bash
# バックエンドのみ再起動
docker-compose restart backend

# フロントエンドのみ再ビルド＆再起動
docker-compose build frontend
docker-compose restart frontend
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs backend
docker-compose logs postgres

# 古いコンテナを削除
docker-compose down
docker-compose up --build
```

### ポートが既に使用されている

```bash
# 既存のプロセスを確認
lsof -i :8000
lsof -i :5173
lsof -i :5432

# または、docker-composeで使用するポートを変更
# docker-compose.ymlの ports: セクションを編集
```

### データベース接続エラー

```bash
# PostgreSQLコンテナの状態確認
docker-compose ps postgres

# PostgreSQLのログ確認
docker-compose logs postgres

# backend/.env の DATABASE_URL を確認
# 正: postgres://chatbrancher:chatbrancher_dev@postgres:5432/chatbrancher
# 誤: postgres://chatbrancher:chatbrancher_dev@localhost:5432/chatbrancher
#     ↑ コンテナ内からはホスト名 "postgres" を使う
```

### コンテナ内のファイルが更新されない

```bash
# ボリュームマウントを確認
docker-compose config

# 完全にクリーンアップして再起動
docker-compose down -v
docker-compose up --build
```

### 原因不明の問題

```bash
# 核オプション：すべてクリーンアップ
docker-compose down -v
docker system prune -a
docker-compose up --build
```

---

## よく使うコマンド早見表

```bash
# 起動
docker-compose up              # フォアグラウンド
docker-compose up -d           # バックグラウンド
docker-compose up --build      # 再ビルドして起動

# 停止
docker-compose down            # コンテナ削除
docker-compose down -v         # ボリュームも削除
docker-compose stop            # コンテナ停止（削除しない）

# ログ
docker-compose logs            # 全ログ
docker-compose logs -f backend # 追跡
docker-compose logs --tail=50  # 最新50行

# コンテナ操作
docker-compose ps              # 状態確認
docker-compose restart backend # 再起動
docker-compose exec backend bash # シェル起動

# マイグレーション
docker-compose exec backend uv run aerich migrate
docker-compose exec backend uv run aerich upgrade
docker-compose exec backend uv run aerich downgrade

# テスト
docker-compose exec backend uv run pytest

# ビルド
docker-compose build           # 全てビルド
docker-compose build backend   # 個別ビルド
```

---

## エディタ設定（VSCode等）

### Python補完のため

ローカルにも依存関係をインストールしておくと、エディタの補完が効きます：

```bash
cd backend
uv sync
```

### Node.js補完のため

```bash
cd frontend
npm install
```

これでVSCodeのIntelliSenseやPylanceが機能します。

---

## 参考情報

- Docker Compose公式ドキュメント: https://docs.docker.com/compose/
- 本番デプロイ手順: `docs/deployment.md`
- プロジェクト概要: メモリファイル参照

---

## まとめ

- **起動**: `docker-compose up -d`
- **停止**: `docker-compose down`
- **コンテナ内コマンド**: `docker-compose exec backend <コマンド>`
- **ログ確認**: `docker-compose logs -f backend`
- **マイグレーション**: `docker-compose exec backend uv run aerich upgrade`

コード編集は今まで通りローカルで行い、保存すれば自動的にコンテナ内に反映されます！
