from abc import ABC, abstractmethod

from domain.entities.message_entity import MessageEntity

class LLMCAdapterProtcol(ABC):
    @abstractmethod
    async def get_response(
        self,
        history:list[MessageEntity],
        model:str,
        temperature:float = 0.7,
        max_tokens:int = 1000
        ) -> dict:
        pass