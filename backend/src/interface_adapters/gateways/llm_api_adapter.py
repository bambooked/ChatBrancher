from infrastructure.openrouter_client import OpenRouterClient
from application.ports.input.llm_adapter import LLMCAdapterProtcol

class LLMAdapter(LLMCAdapterProtcol):
    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client

    def get_response(self):
        self.llm_client.send_and_get()