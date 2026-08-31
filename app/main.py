"""Punto de entrada de la app FastAPI. El health check real (con chequeo de DB) se agrega en el bloque 0.3."""
from fastapi import FastAPI

app = FastAPI(title="PRISM API", version="0.1.0")


# Endpoint raiz minimo, solo para confirmar que el servidor levanta correctamente.
@app.get("/")
def root() -> dict[str, str]:
    return {"service": "prism-backend", "status": "ok"}
