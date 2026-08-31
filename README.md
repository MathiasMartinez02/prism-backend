# PRISM Backend

Backend de PRISM (AI Code Reviewer) construido con FastAPI + PostgreSQL.

Estado: en desarrollo — ver `prism-progreso.md` en el repo raiz del proyecto para el detalle de bloques completados.

## Desarrollo local

```bash
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```
