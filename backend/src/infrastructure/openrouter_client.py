from httpx import AsyncClient, TimeoutException, HTTPStatusError

class OpenRouterClient:
    ""
    BASE_URL = "https://openrouter.ai/api/v1"
    CHAT_ENDPOINT = "/chat/completions"
    MODELS_ENDPOINT = "/models"

    def __init__(self, api_key:str) -> None:
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "null_po",
            "X-Title": "cb_back_v2"
        }

    async def send_and_get(self,
        history:list[dict],
        model:str,
        temperature:float = 0.7,
        max_tokens:int = 1000
        ):
        client = AsyncClient()
        url = f"{self.BASE_URL}{self.CHAT_ENDPOINT}"
        data = {
            "model": model,
            "messages": history,
            "temperature": temperature,  # デフォルト値
            "max_tokens": max_tokens   # デフォルト値
        }
        try:
            response = await client.post(
                url, 
                headers=self.headers, 
                json=data,
            )
            response.raise_for_status()
            response_data = response.json()
            
            return response_data
            
        except TimeoutException:
            raise TimeoutError("LLM API request timed out")
        except HTTPStatusError as e:
            raise ConnectionError(f"LLM API error: {e.response.status_code}")
        except Exception as e:
            raise e