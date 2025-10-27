# Bootstrap版 認証・認可機能 最小実装計画

**作成日:** 2025-10-16
**ステータス:** 計画中
**対象:** Phase 2-A, 2-B, 2-C の簡略版

---

## 目次
1. [背景と運用方針](#背景と運用方針)
2. [実装する機能](#実装する機能)
3. [実装しない機能](#実装しない機能)
4. [具体的な実装内容](#具体的な実装内容)
5. [マイグレーション](#マイグレーション)
6. [開発者用ツール](#開発者用ツール)
7. [運用イメージ](#運用イメージ)
8. [実装手順と工数見積もり](#実装手順と工数見積もり)

---

## 背景と運用方針

### 現状の課題
`docs/require20251015.md` で指摘された問題のうち、データ整合性とマルチユーザー対応に関わる部分のみを解決する。

### Bootstrap版の運用想定
- **マルチユーザー対応**：複数ユーザーが利用可能
- **ユーザー作成**：開発者が手動で作成（コマンドラインツール）
- **認証方式**：パスワード認証（最小限の実装）
  - 開発者がユーザー名・Email・パスワードを設定
  - パスワードはbcryptでハッシュ化して保存
  - AuthenticationServiceは実装しない（フロントエンド側で実装）

### 位置づけ
- ベータ版・クローズドβ運用向け
- 将来的なパスワード認証への拡張は可能な設計
- 最小限の工数で安全なマルチユーザー環境を実現

---

## 実装する機能

### ✅ 1. データ永続化の修正
**目的:** データ整合性の確保
**内容:**
- `ChatTreeDetail` テーブルに `owner_uuid` カラムを追加
- `ChatRepositoryImpl` で `owner_uuid` の保存・取得を実装
- `ChatSelection` で正しい `owner_uuid` を使用

### ✅ 2. ユーザー管理基盤（最小限）
**目的:** マルチユーザー対応の基盤
**内容:**
- `UserModel` の実装（DBテーブル、password_hashフィールド含む）
- `UserRepositoryImpl` の実装（CRUD操作）
- 開発者用のユーザー作成スクリプト

### ✅ 3. パスワードハッシュ化
**目的:** セキュアなパスワード保存
**内容:**
- bcryptを使用したパスワードハッシュ化
- パスワードハッシュ化ユーティリティの実装
- ユーザー作成時のパスワード設定機能

### ✅ 4. シンプルなアクセス制御
**目的:** チャットの不正アクセス防止
**内容:**
- チャット操作時に所有者チェック
- 各ユースケース内で直接チェック（独立したユースケースは作らない）

---

## 実装しない機能

### ❌ 不要なもの
以下は将来的に実装するが、Bootstrap版では不要：

1. **高度な認証機能**
   - AuthenticationService（認証ロジックの抽象化）
   - UserAuthenticationユースケース（ログイン処理）
   - セッション管理・トークン発行

2. **ユーザー自己登録機能**
   - UserRegistrationユースケース
   - Email確認・認証

3. **Value Objects**
   - Email, Username の専用クラス
   - バリデーションロジック

4. **is_active フラグの実際の利用**
   - フィールドは残すが、チェックしない
   - 全ユーザーを `is_active=True` として扱う

5. **VerifyChatAccess ユースケース**
   - 独立したアクセス検証ユースケースは作らない
   - 各ユースケース内で直接チェック

6. **詳細なエラーハンドリング**
   - 専用のExceptionクラス（DomainException等）
   - 既存の `ValueError` で対応

7. **チャット共有機能**
   - Phase 4 の機能（READ/WRITE権限等）

8. **高度な機能**
   - RBAC、監査ログ、セッション管理

---

## 具体的な実装内容

### 📦 1. データベースモデルの追加・修正

#### `backend/src/infrastructure/db/models.py`

**追加: UserModel**
```python
class UserModel(Model):
    uuid = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)  # 追加: bcryptハッシュ
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"
```

**修正: ChatTreeDetail に owner_uuid を追加**
```python
class ChatTreeDetail(Model):
    uuid = fields.UUIDField(pk=True)
    owner_uuid = fields.UUIDField()  # 追加
    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_tree_detail"
```

---

### 📦 1.5. パスワードハッシュ化ユーティリティ

#### `backend/src/infrastructure/security/password.py` (新規作成)

```python
import bcrypt


class PasswordHasher:
    """パスワードのハッシュ化と検証を行うユーティリティ"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        パスワードをbcryptでハッシュ化

        Args:
            password: プレーンテキストのパスワード

        Returns:
            ハッシュ化されたパスワード（文字列）
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        パスワードとハッシュが一致するか検証

        Args:
            password: プレーンテキストのパスワード
            password_hash: ハッシュ化されたパスワード

        Returns:
            一致する場合True、それ以外False
        """
        password_bytes = password.encode('utf-8')
        password_hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, password_hash_bytes)
```

**依存関係の追加:**

`pyproject.toml` に bcrypt を追加：
```toml
[project]
dependencies = [
    # ... 既存の依存関係
    "bcrypt>=4.0.0",
]
```

インストール：
```bash
cd backend
uv pip install bcrypt
```

---

### 📦 2. Repository 実装

#### `backend/src/interface_adapters/gateways/user_repository.py` (新規作成)

```python
from uuid import UUID
from domain.entities.user_entity import UserEntity
from application.ports.output.user_repository import UserRepositoryProtocol
from infrastructure.db.models import UserModel


class UserRepositoryImpl(UserRepositoryProtocol):
    async def save(self, user: UserEntity) -> None:
        """ユーザーを保存（新規作成 or 更新）"""
        await UserModel.update_or_create(
            uuid=UUID(user.uuid),
            defaults={
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            }
        )

    async def find_by_uuid(self, uuid: str) -> UserEntity | None:
        """UUIDでユーザーを取得"""
        try:
            user_model = await UserModel.get(uuid=UUID(uuid))
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active
            )
        except:
            return None

    async def find_by_email(self, email: str) -> UserEntity | None:
        """Emailでユーザーを取得"""
        try:
            user_model = await UserModel.get(email=email)
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active
            )
        except:
            return None

    async def find_by_username(self, username: str) -> UserEntity | None:
        """Usernameでユーザーを取得"""
        try:
            user_model = await UserModel.get(username=username)
            return UserEntity(
                uuid=str(user_model.uuid),
                username=user_model.username,
                email=user_model.email,
                is_active=user_model.is_active
            )
        except:
            return None
```

#### `backend/src/interface_adapters/gateways/chat_repository.py` (修正)

**修正箇所1: ensure_chat_tree_detail()**
```python
async def ensure_chat_tree_detail(self, chat_tree: ChatTreeEntity) -> ChatTreeDetail:
    """チャットツリー詳細を取得または作成（owner_uuid含む）"""
    chat_tree_detail, created = await ChatTreeDetail.get_or_create(
        uuid=chat_tree.uuid,
        defaults={'owner_uuid': UUID(chat_tree.owner_uuid)}  # 追加
    )
    return chat_tree_detail
```

**修正箇所2: 新規メソッド追加**
```python
async def get_chat_tree_info(self, chat_uuid: str) -> dict | None:
    """チャットツリーのメタ情報（owner_uuid含む）を取得"""
    try:
        chat_tree_detail = await ChatTreeDetail.get(uuid=UUID(chat_uuid))
        return {
            'uuid': str(chat_tree_detail.uuid),
            'owner_uuid': str(chat_tree_detail.owner_uuid),
            'created': chat_tree_detail.created,
            'updated': chat_tree_detail.updated
        }
    except:
        return None
```

#### `backend/src/application/ports/output/chat_repository.py` (修正)

**ポート定義に get_chat_tree_info() を追加**
```python
from abc import ABC, abstractmethod

class ChatRepositoryProtocol(ABC):
    # 既存のメソッド...

    @abstractmethod
    async def get_chat_tree_info(self, chat_uuid: str) -> dict | None:
        """チャットツリーのメタ情報（owner_uuid含む）を取得"""
        pass
```

---

### 📦 3. ユースケースの修正（アクセス制御）

#### `backend/src/application/use_cases/chat_selection.py`

**修正箇所1: restart_chat()**
```python
async def restart_chat(self, chat_uuid: str) -> ChatTreeEntity:
    """チャットツリーを再開（アクセス制御付き）"""
    # 1. チャット情報をDBから取得
    chat_info = await self.chat_repository.get_chat_tree_info(chat_uuid)
    if not chat_info:
        raise ValueError(f"Chat tree with ID {chat_uuid} not found")

    # 2. アクセス制御チェック
    if chat_info['owner_uuid'] != self.user.uuid:
        raise ValueError(
            f"Access denied: user {self.user.uuid} does not own chat {chat_uuid}"
        )

    # 3. メッセージリスト取得
    message_list = await self.chat_repository.get_chat_tree_messages(
        chat_uuid, self.user
    )

    # 4. ツリー復元（DBから取得した正しいowner_uuidで）
    self.chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
    self.chat_tree.uuid = UUID(chat_uuid)
    self.chat_tree.owner_uuid = chat_info['owner_uuid']  # 修正：DBから取得

    return self.chat_tree
```

**修正箇所2: get_chat_tree()**
```python
async def get_chat_tree(self, chat_uuid: str) -> ChatTreeEntity:
    """チャットツリーを取得（アクセス制御付き）"""
    # 1. チャット情報をDBから取得
    chat_info = await self.chat_repository.get_chat_tree_info(chat_uuid)
    if not chat_info:
        raise ValueError(f"Chat tree with ID {chat_uuid} not found")

    # 2. アクセス制御チェック
    if chat_info['owner_uuid'] != self.user.uuid:
        raise ValueError(
            f"Access denied: user {self.user.uuid} does not own chat {chat_uuid}"
        )

    # 3. メッセージリスト取得
    message_list = await self.chat_repository.get_chat_tree_messages(
        chat_uuid, self.user
    )

    # 4. ツリー復元（DBから取得した正しいowner_uuidで）
    chat_tree = ChatTreeEntity.restore_from_message_list(message_list)
    chat_tree.uuid = UUID(chat_uuid)
    chat_tree.owner_uuid = chat_info['owner_uuid']  # 修正：DBから取得

    return chat_tree
```

#### `backend/src/application/use_cases/chat_interaction.py`

**修正箇所: send_message_and_get_response()**
```python
async def send_message_and_get_response(
    self, content: str, parent_message: MessageEntity, llm_model: str
) -> MessageEntity:
    """メッセージを送信しLLMレスポンスを取得（アクセス制御付き）"""
    # アクセス制御チェック
    if self.chat_tree.owner_uuid != self.user.uuid:
        raise ValueError(
            f"Access denied: user {self.user.uuid} does not own chat {self.chat_tree.uuid}"
        )

    # 既存の処理...
    if not self._can_add_message_to(parent_message):
        raise ValueError(...)

    # ... 以降の処理は変更なし
```

---

## マイグレーション

### SQLマイグレーション

```sql
-- ========================================
-- Migration: Add users table and owner_uuid to chat_tree_detail
-- Date: 2025-10-16
-- ========================================

-- 1. users テーブル作成
CREATE TABLE users (
    uuid UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. インデックス作成
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 3. chat_tree_detail に owner_uuid カラム追加
ALTER TABLE chat_tree_detail
ADD COLUMN owner_uuid UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';

-- 4. インデックス作成
CREATE INDEX idx_chat_tree_owner ON chat_tree_detail(owner_uuid);

-- 5. デフォルト制約を削除（既存データ対応後）
ALTER TABLE chat_tree_detail
ALTER COLUMN owner_uuid DROP DEFAULT;
```

### aerich での実行手順

```bash
# 1. マイグレーションファイル生成
cd backend
uv run aerich migrate --name "add_users_and_owner_uuid"

# 2. マイグレーション実行
uv run aerich upgrade

# 3. 確認
sqlite3 backend/db.sqlite3
> .schema users
> .schema chat_tree_detail
```

### 既存データの対応

既存のチャットツリーに対しては、デフォルトのユーザーを作成して割り当てる：

```python
# backend/src/scripts/migrate_existing_chats.py
import asyncio
from uuid import uuid4
from infrastructure.db.init_db import init_db
from infrastructure.db.models import UserModel, ChatTreeDetail
from infrastructure.security.password import PasswordHasher

async def migrate_existing_chats():
    await init_db()

    # 1. デフォルトユーザーを作成
    default_user_uuid = uuid4()
    default_password = "default_password_change_me"  # デフォルトパスワード
    password_hash = PasswordHasher.hash_password(default_password)

    await UserModel.create(
        uuid=default_user_uuid,
        username="default_user",
        email="default@example.com",
        password_hash=password_hash,
        is_active=True
    )
    print(f"Created default user: {default_user_uuid}")
    print(f"Default password: {default_password}")

    # 2. 既存のチャットツリーにowner_uuidを設定
    chat_trees = await ChatTreeDetail.filter(
        owner_uuid="00000000-0000-0000-0000-000000000000"
    ).all()

    for chat in chat_trees:
        chat.owner_uuid = default_user_uuid
        await chat.save()

    print(f"Migrated {len(chat_trees)} chat trees")

if __name__ == "__main__":
    asyncio.run(migrate_existing_chats())
```

実行：
```bash
uv run python -m scripts.migrate_existing_chats
```

---

## 開発者用ツール

### ユーザー作成スクリプト

#### `backend/src/scripts/create_user.py` (新規作成)

```python
import asyncio
import sys
import getpass
from uuid import uuid4
from infrastructure.db.init_db import init_db
from infrastructure.db.models import UserModel
from infrastructure.security.password import PasswordHasher


async def create_user(username: str, email: str, password: str) -> str:
    """新規ユーザーを作成"""
    await init_db()

    # 重複チェック
    existing_username = await UserModel.filter(username=username).first()
    if existing_username:
        raise ValueError(f"Username '{username}' already exists")

    existing_email = await UserModel.filter(email=email).first()
    if existing_email:
        raise ValueError(f"Email '{email}' already exists")

    # パスワードをハッシュ化
    password_hash = PasswordHasher.hash_password(password)

    # ユーザー作成
    user_uuid = uuid4()
    await UserModel.create(
        uuid=user_uuid,
        username=username,
        email=email,
        password_hash=password_hash,
        is_active=True
    )

    return str(user_uuid)


async def list_users():
    """登録済みユーザー一覧を表示"""
    await init_db()
    users = await UserModel.all()

    if not users:
        print("No users found.")
        return

    print("\n=== Registered Users ===")
    for user in users:
        status = "Active" if user.is_active else "Inactive"
        print(f"UUID: {user.uuid}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Status: {status}")
        print(f"  Created: {user.created_at}")
        print()


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create user: uv run python -m scripts.create_user create <username> <email>")
        print("  List users:  uv run python -m scripts.create_user list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) != 4:
            print("Error: create command requires <username> and <email>")
            sys.exit(1)

        username = sys.argv[2]
        email = sys.argv[3]

        # パスワード入力（非表示）
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("\n❌ Error: Passwords do not match")
            sys.exit(1)

        if len(password) < 8:
            print("\n❌ Error: Password must be at least 8 characters")
            sys.exit(1)

        try:
            user_uuid = await create_user(username, email, password)
            print(f"\n✅ User created successfully!")
            print(f"UUID: {user_uuid}")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"\n📋 Please provide the username and password to the user for login.")
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    elif command == "list":
        await list_users()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

### 使用方法

```bash
# ユーザー作成
cd backend
uv run python -m scripts.create_user create takeda takeda@example.com

# パスワード入力（非表示）
# Enter password: ********
# Confirm password: ********

# 出力例:
# ✅ User created successfully!
# UUID: 12345678-1234-1234-1234-123456789abc
# Username: takeda
# Email: takeda@example.com
#
# 📋 Please provide the username and password to the user for login.

# ユーザー一覧
uv run python -m scripts.create_user list

# 出力例:
# === Registered Users ===
# UUID: 12345678-1234-1234-1234-123456789abc
#   Username: takeda
#   Email: takeda@example.com
#   Status: Active
#   Created: 2025-10-16 10:30:00
```

---

## 運用イメージ

### 開発者（あなた）の作業フロー

1. **新規ユーザー作成**
   ```bash
   cd backend
   uv run python -m scripts.create_user create user1 user1@example.com
   # パスワード入力を求められる
   ```

2. **ユーザー情報を取得**
   ```
   ✅ User created successfully!
   UUID: 12345678-abcd-efgh-ijkl-123456789012
   Username: user1
   Email: user1@example.com
   ```

3. **ユーザーに認証情報を伝達**
   - Username と Password をユーザーに共有
   - セキュアな方法で伝達（平文メールは避ける）
   - UUIDは内部管理用（ユーザーには不要）

### ユーザーの利用フロー

1. **認証情報を受け取る**
   - 開発者から提供された Username と Password を保管

2. **アプリケーションにログイン**
   - Username/Email と Password を入力してログイン
   - （具体的なログインUIは別途実装）

3. **チャット操作**
   - 自分が作成したチャットのみ表示・編集可能
   - 他ユーザーのチャットにはアクセスできない

### セキュリティ考慮事項

- **パスワードの取り扱い**：
  - bcryptでハッシュ化してDB保存
  - 平文パスワードは保存しない
  - ユーザーへの伝達時は暗号化された通信路を使用
- **パスワードポリシー**：
  - 最小8文字（スクリプトで検証）
  - より厳格なポリシーは将来的に検討
- **セッション管理**：Bootstrap版では未実装（将来的に検討）

---

## 実装手順と工数見積もり

### Phase 1: データベース層の実装

| タスク | 内容 | 工数 |
|--------|------|------|
| 1-1 | bcrypt 依存関係を追加 | 5分 |
| 1-2 | パスワードハッシュ化ユーティリティを実装 | 20分 |
| 1-3 | `UserModel` を追加（password_hash含む） | 15分 |
| 1-4 | `ChatTreeDetail` に `owner_uuid` を追加 | 15分 |
| 1-5 | マイグレーションファイル作成・実行 | 30分 |
| 1-6 | 既存データ移行スクリプト作成・実行 | 30分 |

**小計:** 1時間55分

### Phase 2: Repository 層の実装

| タスク | 内容 | 工数 |
|--------|------|------|
| 2-1 | `UserRepositoryImpl` を作成 | 45分 |
| 2-2 | `ChatRepositoryImpl.ensure_chat_tree_detail()` 修正 | 15分 |
| 2-3 | `ChatRepositoryImpl.get_chat_tree_info()` 追加 | 30分 |
| 2-4 | `ChatRepositoryProtocol` にポート定義を追加 | 15分 |

**小計:** 1時間45分

### Phase 3: ユースケース層の修正

| タスク | 内容 | 工数 |
|--------|------|------|
| 3-1 | `ChatSelection.restart_chat()` 修正 | 30分 |
| 3-2 | `ChatSelection.get_chat_tree()` 修正 | 30分 |
| 3-3 | `ChatInteraction.send_message_and_get_response()` 修正 | 20分 |

**小計:** 1時間20分

### Phase 4: 開発者用ツールの実装

| タスク | 内容 | 工数 |
|--------|------|------|
| 4-1 | ユーザー作成スクリプト作成（パスワード入力機能含む） | 40分 |
| 4-2 | ユーザー一覧スクリプト追加 | 15分 |

**小計:** 55分

### Phase 5: テスト・動作確認

| タスク | 内容 | 工数 |
|--------|------|------|
| 5-1 | ユーザー作成の動作確認 | 15分 |
| 5-2 | チャット作成・再開の動作確認 | 30分 |
| 5-3 | アクセス制御の動作確認 | 30分 |
| 5-4 | 統合テスト（`chat_integ.py`）の修正・実行 | 30分 |

**小計:** 1時間45分

---

### 合計工数

| フェーズ | 工数 |
|----------|------|
| Phase 1: データベース層 | 1時間55分 |
| Phase 2: Repository層 | 1時間45分 |
| Phase 3: ユースケース層 | 1時間20分 |
| Phase 4: 開発者用ツール | 55分 |
| Phase 5: テスト | 1時間45分 |
| **合計** | **約7時間40分** |

---

## 実装チェックリスト

### Phase 1: データベース層
- [ ] bcrypt を `pyproject.toml` に追加してインストール
- [ ] パスワードハッシュ化ユーティリティ `backend/src/infrastructure/security/password.py` を作成
- [ ] `UserModel` を `backend/src/infrastructure/db/models.py` に追加（password_hash含む）
- [ ] `ChatTreeDetail.owner_uuid` を追加
- [ ] マイグレーションファイルを生成（aerich）
- [ ] マイグレーションを実行
- [ ] 既存データ移行スクリプトを実行

### Phase 2: Repository層
- [ ] `backend/src/interface_adapters/gateways/user_repository.py` を新規作成
- [ ] `UserRepositoryImpl` を実装（save, find_by_uuid, find_by_email, find_by_username）
- [ ] `ChatRepositoryImpl.ensure_chat_tree_detail()` を修正
- [ ] `ChatRepositoryImpl.get_chat_tree_info()` を追加
- [ ] `ChatRepositoryProtocol` にポート定義を追加

### Phase 3: ユースケース層
- [ ] `ChatSelection.restart_chat()` を修正
- [ ] `ChatSelection.get_chat_tree()` を修正
- [ ] `ChatInteraction.send_message_and_get_response()` を修正

### Phase 4: 開発者用ツール
- [ ] `backend/src/scripts/create_user.py` を新規作成
- [ ] create コマンドを実装（パスワード入力機能含む）
- [ ] list コマンドを実装

### Phase 5: テスト
- [ ] ユーザー作成スクリプトの動作確認
- [ ] チャット作成の動作確認
- [ ] チャット再開の動作確認
- [ ] アクセス制御の動作確認
- [ ] 統合テスト（`chat_integ.py`）を修正・実行

---

## 今後の拡張ポイント

Bootstrap版実装後、必要に応じて以下を追加できる：

### 短期的な拡張
- ユーザー無効化機能（`is_active` フラグの活用）
- ユーザー情報の更新（username, email）
- ユーザー削除機能

### 中期的な拡張
- AuthenticationServiceの実装（認証ロジックの抽象化）
- セッション管理
- トークンベース認証（JWT）
- より厳格なパスワードポリシー

### 長期的な拡張
- チャット共有機能
- ロールベースアクセス制御（RBAC）
- 監査ログ

---

## 参考資料

- **元ドキュメント:** `docs/require20251015.md`
- **Domain層:** `backend/src/domain/entities/`
- **Application層:** `backend/src/application/use_cases/`
- **Infrastructure層:** `backend/src/infrastructure/db/models.py`
- **既存テスト:** `backend/src/tests/dev/chat_integ.py`

---

**最終更新:** 2025-10-16
**作成者:** Claude Code
**レビュー:** 未実施
