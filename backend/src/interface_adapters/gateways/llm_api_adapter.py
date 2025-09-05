from infrastructure.openrouter_client import OpenRouterClient
from application.ports.input.llm_adapter import LLMCAdapterProtcol
from domain.entities.message_entity import MessageEntity
from interface_adapters.presenters.format_llm_input import trasnport_message_entity
from interface_adapters.presenters.format_lllm_output import flat_api_response

class LLMAdapter(LLMCAdapterProtcol):
    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client

    async def get_response(self,
        history:list[MessageEntity],
        model:str,
        temperature:float = 0.7,
        max_tokens:int = 1000
        ):
        transed_history = trasnport_message_entity(history)
        response = await self.llm_client.send_and_get(
            transed_history,
            model,
            temperature,
            max_tokens
            )
        formatted_responce = flat_api_response(response)
        
        return formatted_responce