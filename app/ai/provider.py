"""Interfaz abstracta que cualquier proveedor de AI (Gemini, Ollama, ...) debe implementar."""
from abc import ABC, abstractmethod

from app.schemas.finding import FindingCreate


class AIProvider(ABC):
    # Analiza un hunk de diff (con contexto alrededor) y devuelve la lista de findings detectados.
    @abstractmethod
    async def analyze_hunk(self, file_path: str, diff_hunk: str, context: str = "") -> list[FindingCreate]:
        ...
