import anthropic

from config import settings
from providers.base_interface import AIProvider


class CloudProvider(AIProvider):
    """Calls Anthropic's API — used only for the comparative evaluation."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    async def complete(self, prompt: str) -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def health_check(self) -> bool:
        return bool(settings.anthropic_api_key)
