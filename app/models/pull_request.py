"""Modelo de un Pull Request traido desde GitHub."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.repository import Repository


# PullRequest representa un PR de GitHub asociado a un repositorio conectado.
class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        # Evita duplicar el mismo PR si se vuelve a sincronizar el repo (idempotencia).
        UniqueConstraint("repository_id", "github_pr_number", name="uq_pull_requests_repo_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repository: Mapped["Repository"] = relationship(back_populates="pull_requests")
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="pull_request", cascade="all, delete-orphan"
    )
