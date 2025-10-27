# Renderデプロイ評価

本ドキュメントは、ChatBrancher を render.com へ Docker デプロイする際の実現性を評価し、現状の課題と推奨対応策を整理したものです。

## バックエンド
- Python 要件が `>=3.13` (`backend/pyproject.toml:6`) だが、Render の標準ランタイムは 3.12 まで。要件の引き下げまたは Python 3.13 を含むカスタムベースイメージの用意が必要。
- 永続化先が SQLite (`backend/src/infrastructure/db/config.py:10`) でコンテナ内ファイルを参照。Render のコンテナファイルシステムは再デプロイで消えるため、Persistent Disk の利用か Render マネージド Postgres への移行を検討すべき。
- Uvicorn は Render から渡される `PORT` 環境変数でバインドする必要がある。起動コマンド例: `uvicorn main:app --host 0.0.0.0 --port ${PORT}`。
- `SECRET_KEY` や `OPENROUTER_API_KEY` などの秘密情報は `backend/src/infrastructure/config.py:9` で `.env` 読み込みに頼っている。Render 環境変数から注入する構成へ切り替える。
- Aerich マイグレーションを実行する仕組みが未整備。デプロイ後に `aerich upgrade` を走らせるリリースコマンドやジョブを設計する。

## フロントエンド
- API クライアントが `http://localhost:8000` に固定 (`frontend/src/routes/login/+page.svelte:11` ほか)。Render 上では環境変数等から API ベース URL を注入できるようリファクタリングが必要。
- SvelteKit が `@sveltejs/adapter-auto` (`frontend/svelte.config.js:9`) を利用しており、Render のコンテナ向きではない。`adapter-node` か `adapter-static` への切り替えを推奨。
- リポジトリに `frontend/node_modules` が含まれており Docker コンテキストが肥大化する。`.dockerignore` を用意して不要ファイルを除外する。

## コンテナおよびインフラ構成
- バックエンドとフロントエンドは別コンテナ/サービスとしてデプロイする構成が自然。単一コンテナで提供する場合はリバースプロキシとプロセスマネージャを整備する必要がある。
- マルチステージ Dockerfile を用いて実行時イメージをスリム化する（例: backend は `uv pip install --no-dev`、frontend は `npm ci && npm run build` 後に成果物のみコピー）。
- OpenRouter など外部 API への通信が Render から可能かを事前確認し、再試行やレート制限対策を実装する。
- Render 用に環境変数定義、サービス構成 (`render.yaml` など) を早期に作成し、ローカルで `docker compose` 等による検証を行うと移行が楽になる。

## 推奨アクション
1. 対象ランタイム（Python バージョン・データベース）を決定し、それに合わせて依存関係と接続設定を更新する。
2. フロントエンドの API ベース URL を環境変数駆動へ変更し、SvelteKit アダプタを Render 向けに切り替える。
3. バックエンド・フロントエンドそれぞれの Dockerfile と `.dockerignore` を作成し、起動コマンドおよびマイグレーション実行フローを整備する。
4. Render の環境変数設定や Persistent Disk / Postgres 構成、リリースコマンドの設計を進め、ローカルでビルド・起動検証を行う。
