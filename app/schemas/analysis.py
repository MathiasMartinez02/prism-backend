"""Schemas de respuesta para el recurso analysis (y sus findings anidados)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    severity: str
    file_path: str
    line_number: int | None
    description: str
    recommendation: str | None


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    overall_score: int | None
    ai_provider: str | None
    started_at: datetime | None
    finished_at: datetime | None
    findings: list[FindingOut]
