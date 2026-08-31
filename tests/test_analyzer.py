"""Tests de analyzer con un AIProvider fake (no llama a ningun modelo real)."""
import pytest

from app.ai.provider import AIProvider
from app.schemas.finding import FindingCreate
from app.services.analyzer import analyze_diff

REAL_DIFF = """diff --git a/app/services/scorer.py b/app/services/scorer.py
index 3333333..4444444 100644
--- a/app/services/scorer.py
+++ b/app/services/scorer.py
@@ -1,3 +1,5 @@
 def calculate_score(findings):
+    if not findings:
+        return 100
     score = 100
     return max(score, 0)
diff --git a/app/utils/math.py b/app/utils/math.py
index 5555555..6666666 100644
--- a/app/utils/math.py
+++ b/app/utils/math.py
@@ -1,2 +1,4 @@
 def average(numbers):
+    total = sum(numbers)
+    unused = 1
     return sum(numbers) / len(numbers)
"""


# Provider fake: devuelve un finding fijo por cada hunk que le llega, sin llamar a ninguna API.
class FakeProvider(AIProvider):
    def __init__(self):
        self.calls: list[str] = []

    async def analyze_hunk(self, file_path: str, diff_hunk: str, context: str = "") -> list[FindingCreate]:
        self.calls.append(file_path)
        return [FindingCreate(category="quality", severity="low", file_path=file_path, description="finding fake")]


@pytest.mark.asyncio
async def test_analyze_diff_returns_empty_list_for_empty_diff():
    provider = FakeProvider()

    findings = await analyze_diff(provider, "")

    assert findings == []
    assert provider.calls == []


@pytest.mark.asyncio
async def test_analyze_diff_calls_provider_once_per_relevant_hunk():
    provider = FakeProvider()

    findings = await analyze_diff(provider, REAL_DIFF)

    assert sorted(provider.calls) == ["app/services/scorer.py", "app/utils/math.py"]
    assert len(findings) == 2


@pytest.mark.asyncio
async def test_analyze_diff_skips_irrelevant_files_before_calling_provider():
    provider = FakeProvider()
    diff_with_lockfile = REAL_DIFF + """diff --git a/package-lock.json b/package-lock.json
index 1111111..2222222 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,3 +1,3 @@
 {
-  "version": "1.0.0"
+  "version": "1.0.1"
 }
"""

    await analyze_diff(provider, diff_with_lockfile)

    assert "package-lock.json" not in provider.calls
