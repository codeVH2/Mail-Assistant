from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Unified interface for local and cloud AI providers."""

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Send a prompt and return the model's text response."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""
        ...
