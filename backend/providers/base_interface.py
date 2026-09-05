from abc import ABC, abstractmethod

class AIProvider(ABC):
    """Unified interface for local and cloud AI providers."""
    name: str  # e.g. "local" or "cloud"
    model: str  # e.g. "llama3.1:8b" or "claude-sonnet-4-6"
    
    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Send a prompt and return the model's text response."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""
        ...
