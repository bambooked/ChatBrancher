from tortoise.models import Model
from tortoise import fields
from src.domain.entities.message_entity import Role


class MessageModel(Model):
    """
    メッセージのTortoiseモデル（隣接リスト形式による木構造管理）
    
    Attributes:
        uuid: メッセージの一意識別子（主キー）
        role: メッセージの送信者役割
        content: メッセージ内容
        parent: 親メッセージ参照（ルートメッセージの場合はNone）
        created_at: 作成日時
        updated_at: 更新日時
    """
    uuid = fields.UUIDField(pk=True)
    role = fields.CharEnumField(Role)
    content = fields.TextField()
    parent = fields.ForeignKeyField(
        'models.MessageModel', 
        related_name='children',
        null=True,
        on_delete=fields.CASCADE
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "messages"