from typing import Protocol

from domain.entities.message_entity import MessageEntity

class LLMCAdapterProtcol(Protocol):
    async def get_response(
        self,
        history:list[MessageEntity],
        model:str,
        temperature:float = 0.7,
        max_tokens:int = 1000
        ):
        print("this is protocl, not implement!")
        return "hoge"