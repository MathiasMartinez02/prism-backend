"""Parsea un diff unificado en hunks estructurados, filtrando archivos irrelevantes."""
from dataclasses import dataclass

from unidiff import PatchSet

# Lockfiles: cambian solo por versionado de dependencias, nunca aportan un finding real.
_IGNORED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "gemfile.lock",
    "go.sum",
    "composer.lock",
    "cargo.lock",
}

# Extensiones binarias o de assets: no tiene sentido mandarle esto al modelo como "codigo".
_IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp",
    ".pdf", ".zip", ".tar", ".gz",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".mp3", ".mov",
}

# Carpetas de output/generado: si aparecen en el diff no son codigo escrito a mano.
_IGNORED_PATH_SEGMENTS = {
    "node_modules/", "dist/", "build/", ".next/", "__pycache__/",
    "coverage/", "vendor/", ".venv/", "venv/",
}


# Un hunk listo para mandarle al AIProvider: el archivo al que pertenece y el texto del hunk con contexto.
@dataclass
class Hunk:
    file_path: str
    content: str
    added_lines: int
    removed_lines: int


# Decide si un archivo del diff vale la pena analizar (no es lockfile/asset/binario/generado).
def is_relevant_file(file_path: str) -> bool:
    filename = file_path.rsplit("/", 1)[-1].lower()
    if filename in _IGNORED_FILENAMES:
        return False

    extension = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    if extension in _IGNORED_EXTENSIONS:
        return False

    lowered_path = file_path.lower()
    if any(segment in lowered_path for segment in _IGNORED_PATH_SEGMENTS):
        return False

    return True


# Convierte el diff crudo de un PR en la lista de hunks relevantes para analizar.
def parse_diff(diff_text: str) -> list[Hunk]:
    if not diff_text.strip():
        return []

    patch_set = PatchSet(diff_text)
    hunks: list[Hunk] = []

    for patched_file in patch_set:
        if patched_file.is_binary_file:
            continue
        if not is_relevant_file(patched_file.path):
            continue

        for hunk in patched_file:
            hunks.append(
                Hunk(
                    file_path=patched_file.path,
                    content=str(hunk),
                    added_lines=hunk.added,
                    removed_lines=hunk.removed,
                )
            )

    return hunks
