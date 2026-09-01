"""Orquesta correr un analisis completo sobre un PR: traer diff, analizar, scorear y persistir."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.ai.prompts import PROMPT_VERSION
from app.core.config import settings
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.pull_request import PullRequest
from app.services import github_client
from app.services.analyzer import analyze_diff
from app.services.scorer import calculate_score


# Se levanta cuando no hay nada que analizar (el PR no tiene diff_url guardada).
class AnalysisError(Exception):
    pass


# Corre el pipeline completo para un PR ya persistido: trae el diff real de GitHub, lo manda
# al AIProvider configurado, calcula el score y guarda todo (Analysis + Findings) en la DB.
# Si algo falla, la Analysis queda igual guardada con status='failed' y el error registrado
# (documentar el fallo es tan importante como documentar el exito para debuggear despues).
async def run_analysis(db: Session, pull_request: PullRequest) -> Analysis:
    if not pull_request.diff_url:
        raise AnalysisError(f"pull request {pull_request.id} no tiene diff_url")

    analysis = Analysis(
        pull_request_id=pull_request.id,
        status="running",
        started_at=datetime.now(UTC),
        prompt_version=PROMPT_VERSION,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        provider = get_ai_provider()
        diff_text = await github_client.get_diff(pull_request.diff_url)
        findings = await analyze_diff(provider, diff_text)
        score = calculate_score(findings)

        for finding in findings:
            db.add(
                Finding(
                    analysis_id=analysis.id,
                    category=finding.category,
                    severity=finding.severity,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    description=finding.description,
                    recommendation=finding.recommendation,
                )
            )

        analysis.status = "completed"
        analysis.overall_score = score
        analysis.ai_provider = settings.ai_provider
        analysis.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(analysis)
        return analysis

    except Exception as exc:
        db.rollback()
        analysis.status = "failed"
        analysis.error_message = str(exc)
        analysis.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(analysis)
        raise
