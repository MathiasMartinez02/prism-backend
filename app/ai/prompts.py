"""Templates de prompt versionados. Cambiar el contenido del prompt implica subir PROMPT_VERSION."""

# Se guarda en analyses.ai_provider/prompt_version (bloque 2.4) para poder debuggear a futuro
# por que salio raro un finding, sabiendo con que version de prompt se genero.
PROMPT_VERSION = "v1"

_ANALYSIS_INSTRUCTIONS = """You are a senior code reviewer analyzing a single diff hunk from a Pull Request.

Look only at what changed in this hunk (lines starting with + or -). Use the surrounding context only to understand intent, not to report issues that already existed before this change.

Report findings in these categories only: bug, security, performance, quality, tests.
Use severity: low, medium, high.

Respond with ONLY a JSON array (no markdown, no prose, no code fences). Each element must have exactly these fields:
- category: one of "bug", "security", "performance", "quality", "tests"
- severity: one of "low", "medium", "high"
- file_path: the file path given below
- line_number: the line number in the NEW version of the file where the issue is, or null if not applicable
- description: one clear sentence describing the issue
- recommendation: one clear sentence with how to fix it, or null

If there are no issues, respond with an empty JSON array: []
"""


# Arma el prompt final para un hunk puntual, listo para mandarle al AIProvider.
def build_analysis_prompt(file_path: str, diff_hunk: str, context: str = "") -> str:
    parts = [
        _ANALYSIS_INSTRUCTIONS,
        f"\nFile: {file_path}",
    ]
    if context:
        parts.append(f"\nContext:\n{context}")
    parts.append(f"\nDiff hunk:\n{diff_hunk}")
    return "\n".join(parts)


# Prompt correctivo usado en el retry cuando la primera respuesta no parseo como JSON valido.
def build_retry_prompt(original_prompt: str, invalid_response: str) -> str:
    return (
        f"{original_prompt}\n\n"
        f"Your previous response was not valid JSON matching the schema above:\n{invalid_response}\n\n"
        "Respond again with ONLY the corrected JSON array, nothing else."
    )
