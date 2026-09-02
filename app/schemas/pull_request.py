"""Schemas Pydantic de request/response para el recurso pull_request."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Forma en la que se devuelve un PR ya persistido en la respuesta del endpoint.
class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    github_pr_number: int
    title: str
    author: str | None
    diff_url: str | None
    created_at: datetime


# Resumen del ultimo analisis de un PR, embebido en el listado.
class LatestAnalysisSummary(BaseModel):
    id: uuid.UUID
    status: str
    overall_score: int | None
    findings_count: int
    high_severity_count: int
    category_counts: dict[str, int]  # ej. {"bug": 1, "performance": 2}


# PR + su ultimo analisis (si tiene alguno), para la tabla del dashboard.
class PullRequestListItemOut(PullRequestOut):
    latest_analysis: LatestAnalysisSummary | None = None
