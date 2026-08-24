from config import settings
from providers.base_interface import AIProvider
from providers.cloud_provider import CloudProvider
from providers.local_provider import LocalProvider


def get_provider(name: str | None = None) -> AIProvider:
    if name is None:
        name = "local"      # local by default

    if name == "cloud":
        return CloudProvider()
    return LocalProvider()

