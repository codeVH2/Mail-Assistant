from config import settings
from providers.base_interface import AIProvider
from providers.cloud_provider import CloudProvider
from providers.local_provider import LocalProvider


def get_provider() -> AIProvider:
    if settings.ai_provider == "cloud":
        return CloudProvider()
    return LocalProvider()
