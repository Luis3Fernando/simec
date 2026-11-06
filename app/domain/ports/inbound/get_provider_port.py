from abc import ABC, abstractmethod

from app.domain.models.provider import ProviderReport


class GetProviderPort(ABC):
    @abstractmethod
    async def get_provider(self, tax_id: str) -> ProviderReport: ...
