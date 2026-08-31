FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema minimas para psycopg (driver de Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
# alembic.ini se agrega en el bloque 0.4 (init de Alembic); hasta entonces esta carpeta viaja vacia.

RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
