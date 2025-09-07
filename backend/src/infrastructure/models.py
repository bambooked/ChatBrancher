from tortoise.models import Model
from tortoise import fields
from src.domain.entities.message_entity import Role


class MessageModel(Model):
    """
    メッセージのTortoiseモデル（シンプル版：メモリ上で木構造操作）
    
    Attributes:
        uuid: メッセージの一意識別子（主キー）
        role: メッセージの送信者役割
        content: メッセージ内容
        parent_uuid: 親メッセージのUUID（ルートメッセージの場合はNone）
        chat_tree_id: チャット木のグループ識別子
        user_context_id: ユーザーコンテキストID（将来の所有者管理用）
        created_at: 作成日時
        updated_at: 更新日時
    """
    uuid = fields.UUIDField(pk=True)
    role = fields.CharEnumField(Role)
    content = fields.TextField()
    parent_uuid = fields.UUIDField(null=True)
    chat_tree_id = fields.UUIDField()
    user_context_id = fields.UUIDField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "messages"


class AssistantMessageDetail(Model):
    """
    アシスタントメッセージの詳細情報（LLM関連データ）
    
    Attributes:
        message: 対応するメッセージモデル（1対1関係）
        provider: LLMプロバイダー名
        model_name: 使用したLLMモデル名
        prompt_tokens: プロンプトトークン数
        completion_tokens: 完了トークン数
        total_tokens: 総トークン数
        temperature: 使用した温度設定
        max_tokens: 最大トークン設定
        finish_reason: 完了理由
        gen_id: LLM生成ID
        object_: レスポンスオブジェクト種別
        created_timestamp: LLMでの作成タイムスタンプ
    """
    message = fields.OneToOneField('models.MessageModel', pk=True, on_delete=fields.CASCADE)
    provider = fields.CharField(max_length=50, null=True)
    model_name = fields.CharField(max_length=100, null=True)
    prompt_tokens = fields.IntField(default=0)
    completion_tokens = fields.IntField(default=0)
    total_tokens = fields.IntField(default=0)
    temperature = fields.FloatField(null=True)
    max_tokens = fields.IntField(null=True)
    finish_reason = fields.CharField(max_length=50, null=True)
    gen_id = fields.CharField(max_length=255, null=True)
    object_ = fields.CharField(max_length=50, null=True)
    created_timestamp = fields.CharField(max_length=50, null=True)
    
    class Meta:
        table = "assistant_message_details"