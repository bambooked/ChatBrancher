from interface_adapters.gateways.llm_api_adapter import LLMAdapter
from infrastructure.openrouter_client import OpenRouterClient

from dotenv import load_dotenv
load_dotenv()

from os import getenv

from domain.entities.message_entity import MessageEntity
client = OpenRouterClient(getenv("OPENROUTER_API_KEY"))
adapter = LLMAdapter(client)
# テスト用のhistoryを作成
history = [
    MessageEntity.create_system_message("あなたは親切なAIアシスタントです。"),
    MessageEntity.create_user_message("こんにちは！今日の天気について教えてください。"),
    MessageEntity.create_assistant_message("こんにちは！申し訳ございませんが、私は現在の天気情報にアクセスできません。最新の天気予報については、天気予報サイトやアプリをご確認ください。"),
    MessageEntity.create_user_message("わかりました。では、今日何か良いことがありそうですか？")
]

import asyncio

# デバッグ用：historyが正しく変換されるかチェック
from interface_adapters.presenters.format_llm_input import trasnport_message_entity
converted_history = trasnport_message_entity(history)

# asyncio.run()を使用してasync関数を実行
try:
    result = asyncio.run(adapter.get_response(history, "anthropic/claude-3-haiku"))
    print("結果:")
    print(result)
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print(f"エラーの型: {type(e)}")