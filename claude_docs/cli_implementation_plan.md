# ChatBrancher CLI 実装計画書

## 概要

ChatBrancherバックエンドの既存メソッドを活用した、ターミナル操作用CLIアプリケーションの実装計画です。

## 前提条件

- astral/uvを使用したPython環境
- 既存のバックエンドアーキテクチャ（`ChatInteraction`クラス）を最大限活用
- エクスポート機能は不要（既存メソッドで対応不可能なため除外）
- 新規ファイル作成は最小限に抑制

## 利用可能な既存メソッド

### ChatInteractionクラス（backend/src/application/use_cases/chat_interaction.py）

1. `start_chat(initial_message: str) -> ChatTreeEntity`
   - 新しいチャットセッションを初期化
   
2. `restart_chat(parent_message: MessageEntity) -> ChatTreeEntity`
   - 既存メッセージから新しいブランチを作成
   
3. `send_message_and_get_response(content: str, parent_message: MessageEntity, llm_model: str) -> MessageEntity`
   - メッセージ送信とLLM応答の一括処理
   
4. `get_chat_list() -> list[str]`
   - 全チャットID一覧取得
   
5. `get_chat_tree(chat_uuid: str) -> ChatTreeEntity`
   - 指定チャットツリーの復元

## CLI設計案

### コマンド構造

```
uv run python -m backend.src.cli [COMMAND] [OPTIONS]

COMMANDS:
  chat      チャットセッション操作
  list      チャット一覧表示
  tree      チャットツリー可視化
```

### 具体的なコマンド仕様

#### 1. `chat` コマンド群

```bash
# 新しいチャット開始
uv run python -m backend.src.cli chat start "初期システムメッセージ"
# → ChatInteraction.start_chat() を使用

# チャットに参加（対話モード）
uv run python -m backend.src.cli chat join <chat_uuid>
# → ChatInteraction.get_chat_tree() でツリー取得後、対話開始

# 単発メッセージ送信
uv run python -m backend.src.cli chat send <parent_message_uuid> "メッセージ内容" --model "gpt-4o"
# → ChatInteraction.send_message_and_get_response() を使用

# チャット再開（新ブランチ作成）
uv run python -m backend.src.cli chat restart <parent_message_uuid>
# → ChatInteraction.restart_chat() を使用
```

#### 2. `list` コマンド

```bash
# 全チャット一覧
uv run python -m backend.src.cli list
# → ChatInteraction.get_chat_list() を使用

# チャット詳細表示
uv run python -m backend.src.cli list <chat_uuid> --details
# → ChatInteraction.get_chat_tree() でツリー取得後、詳細情報表示
```

#### 3. `tree` コマンド

```bash
# チャットツリー可視化
uv run python -m backend.src.cli tree <chat_uuid>
# → ChatInteraction.get_chat_tree() でツリー取得後、rich.treeで表示

# 特定メッセージ以降のサブツリー表示
uv run python -m backend.src.cli tree <chat_uuid> --from <message_uuid>
# → 取得したツリーから指定メッセージ以降を抽出して表示
```

## 実装ファイル構造

```
backend/src/cli/
├── __main__.py          # エントリーポイント
├── commands/
│   ├── __init__.py
│   ├── chat.py          # チャット関連コマンド
│   ├── list_cmd.py      # 一覧表示コマンド
│   └── tree.py          # ツリー表示コマンド
├── display/
│   ├── __init__.py
│   ├── formatters.py    # 出力フォーマッター
│   └── tree_renderer.py # ツリー可視化
├── utils/
│   ├── __init__.py
│   └── async_helpers.py # 非同期処理ヘルパー
└── config.py            # CLI設定管理
```

## 技術的実装詳細

### 必要な新規依存関係

```toml
# pyproject.tomlに追加
click = "^8.1.0"    # CLIフレームワーク
rich = "^13.0.0"    # リッチテキスト表示
```

### 非同期処理の統合

既存のバックエンドメソッドが非同期なため、CLIでは以下のパターンを使用：

```python
import asyncio
from backend.src.application.use_cases.chat_interaction import ChatInteraction

def async_command_wrapper(async_func):
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return wrapper
```

### UUIDの簡略化

- フルUUID（36文字）の代わりに、最初の8文字での識別を提供
- 曖昧な場合は候補一覧を表示して選択を促す

### 出力フォーマット

1. **一覧表示**: テーブル形式（rich.tableを使用）
2. **ツリー表示**: 分岐構造の可視化（rich.treeを使用）
3. **メッセージ表示**: ユーザー/アシスタントで色分け

## 実装手順（TDD準拠）

### Phase 1: 基本CLI構造
1. エントリーポイントとコマンドグループの作成
2. 既存のChatInteractionとの接続確認
3. 基本的なエラーハンドリング

### Phase 2: listコマンド実装
1. `list`コマンドの基本機能
2. チャット詳細表示の実装

### Phase 3: chatコマンド実装
1. `chat start`サブコマンド
2. `chat send`サブコマンド
3. `chat join`対話モード
4. `chat restart`サブコマンド

### Phase 4: treeコマンド実装
1. ツリー構造の可視化
2. サブツリー表示機能

### Phase 5: UX改善
1. UUID短縮表示機能
2. エラーメッセージの改善
3. ヘルプドキュメントの充実

## 注意事項

- **既存コード変更なし**: 既存のバックエンドコードは一切変更しない
- **依存関係の最小化**: 必要最小限の外部ライブラリのみ追加
- **エラーハンドリング**: 既存メソッドの例外をCLIレベルで適切に処理
- **環境設定**: `.env`ファイルの読み込みをCLI側で実装

## 使用例

```bash
# 新規チャット開始
uv run python -m backend.src.cli chat start "あなたはプログラミングアシスタントです"
# Output: Chat started with ID: abc12345 (System message added)

# チャット一覧確認
uv run python -m backend.src.cli list
# Output: 
# ID       Created     Messages
# abc12345 2024-01-15  1
# def67890 2024-01-14  5

# メッセージ送信
uv run python -m backend.src.cli chat send abc12345 "Pythonの基本について教えて" --model "gpt-4o"
# Output: 
# [User] Pythonの基本について教えて
# [Assistant] Pythonは...（LLM応答）
# Message ID: xyz98765

# ツリー表示
uv run python -m backend.src.cli tree abc12345
# Output: (ツリー構造の可視化)
```

この計画書は、既存のバックエンドアーキテクチャを最大限活用しながら、実用的なCLIインターフェースを提供することを目的としています。