"""Schema del finding tal como lo devuelve (en JSON) un AIProvider, antes de persistirlo."""
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["bug", "security", "performance", "quality", "tests"]
Severity = Literal["low", "medium", "high"]


# Forma exacta que le exigimos al modelo por cada finding, validada al parsear su respuesta.
class FindingCreate(BaseModel):
    category: Category
    severity: Severity
    file_path: str
    line_number: int | None = None
    description: str = Field(min_length=1)
    recommendation: str | None = None
