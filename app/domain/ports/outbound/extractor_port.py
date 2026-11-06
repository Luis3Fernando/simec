from abc import ABC, abstractmethod
from typing import Any


class ExtractorPort(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def extract(self, parameter: str) -> dict[str, Any]: ...
