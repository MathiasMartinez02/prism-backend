# Importa los modelos para que se registren en Base.metadata.
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.pull_request import PullRequest
from app.models.repository import Repository

__all__ = ["Analysis", "Finding", "PullRequest", "Repository"]
