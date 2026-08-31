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
