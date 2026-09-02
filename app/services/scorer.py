"""Calcula el score agregado de un analisis a partir de sus findings."""
from collections import Counter

from app.schemas.finding import FindingCreate

# Puntos que se restan por finding, segun categoria y severidad.
_PENALTIES: dict[str, dict[str, int] | int] = {
    "bug": {"high": 15, "medium": 8, "low": 3},
    "security": {"high": 20, "medium": 10, "low": 5},
    "performance": 5,
    "quality": 2,
    "tests": 2,
}


# score = 100 - penalizaciones, nunca por debajo de 0.
def calculate_score(findings: list[FindingCreate]) -> int:
    score = 100

    for finding in findings:
        penalty = _PENALTIES.get(finding.category, 0)
        if isinstance(penalty, dict):
            score -= penalty.get(finding.severity, 0)
        else:
            score -= penalty

    return max(score, 0)


# Cuenta findings por categoria.
def count_by_category(findings: list[FindingCreate]) -> dict[str, int]:
    return dict(Counter(finding.category for finding in findings))
