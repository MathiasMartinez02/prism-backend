"""Schema de las stats agregadas de un repositorio, para las stat cards del dashboard."""
from pydantic import BaseModel


class RepositoryStats(BaseModel):
    total_analyzed: int  # cantidad de PRs con al menos un analisis completado
    average_score: float | None  # promedio del ultimo score de cada PR analizado
    critical_findings: int  # suma de findings de severidad alta, entre los ultimos analisis
    ai_provider: str  # provider configurado actualmente (AI_PROVIDER)
