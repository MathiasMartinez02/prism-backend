"""Tests de scorer: facil de testear sin mockear AI, como marca la guia de desarrollo."""
from app.schemas.finding import FindingCreate
from app.services.scorer import calculate_score, count_by_category


def _finding(category: str, severity: str = "low") -> FindingCreate:
    return FindingCreate(category=category, severity=severity, file_path="x.py", description="x")


def test_calculate_score_is_100_with_no_findings():
    assert calculate_score([]) == 100


def test_calculate_score_penalizes_high_severity_bug():
    assert calculate_score([_finding("bug", "high")]) == 85


def test_calculate_score_penalizes_high_severity_security_more_than_bug():
    assert calculate_score([_finding("security", "high")]) == 80


def test_calculate_score_combines_multiple_findings():
    findings = [
        _finding("bug", "high"),  # -15
        _finding("bug", "medium"),  # -8
        _finding("performance"),  # -5
        _finding("quality"),  # -2
    ]
    assert calculate_score(findings) == 100 - 15 - 8 - 5 - 2


def test_calculate_score_never_goes_below_zero():
    findings = [_finding("security", "high") for _ in range(10)]
    assert calculate_score(findings) == 0


def test_count_by_category_groups_correctly():
    findings = [_finding("bug"), _finding("bug"), _finding("performance")]
    assert count_by_category(findings) == {"bug": 2, "performance": 1}


def test_count_by_category_returns_empty_dict_for_no_findings():
    assert count_by_category([]) == {}
