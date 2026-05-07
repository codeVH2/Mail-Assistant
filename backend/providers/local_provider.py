import httpx

from config import settings
from providers.base_interface import AIProvider


class LocalProvider(AIProvider):
    """Calls Ollama running locally — email content never leaves the machine."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
