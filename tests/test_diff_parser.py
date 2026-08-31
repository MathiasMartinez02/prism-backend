"""Tests de diff_parser con diffs reales/realistas guardados como fixtures (sin mockear AI)."""
from pathlib import Path

from app.services.diff_parser import is_relevant_file, parse_diff

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_parse_diff_returns_empty_list_for_empty_diff():
    assert parse_diff("") == []
    assert parse_diff("   \n  ") == []


def test_parse_diff_extracts_hunks_from_real_pr_diff():
    diff_text = _read_fixture("real_pr.diff")

    hunks = parse_diff(diff_text)

    file_paths = {hunk.file_path for hunk in hunks}
    assert file_paths == {"index.html", "styles.css"}
    assert len(hunks) == 2
    assert all(hunk.added_lines > 0 for hunk in hunks)


def test_parse_diff_filters_out_lockfile_but_keeps_relevant_file():
    diff_text = _read_fixture("lockfile_and_relevant.diff")

    hunks = parse_diff(diff_text)

    assert len(hunks) == 1
    assert hunks[0].file_path == "app/services/scorer.py"


def test_parse_diff_filters_out_binary_files():
    diff_text = _read_fixture("binary_file.diff")

    hunks = parse_diff(diff_text)

    assert hunks == []


def test_parse_diff_handles_pure_rename_without_crashing():
    diff_text = _read_fixture("renamed_file.diff")

    hunks = parse_diff(diff_text)

    # Un rename puro no trae hunks de contenido, pero no debe romper el parser.
    assert hunks == []


def test_is_relevant_file_rejects_known_lockfiles_and_assets():
    assert is_relevant_file("package-lock.json") is False
    assert is_relevant_file("frontend/yarn.lock") is False
    assert is_relevant_file("assets/logo.png") is False
    assert is_relevant_file("node_modules/react/index.js") is False


def test_is_relevant_file_accepts_source_files():
    assert is_relevant_file("app/services/scorer.py") is True
    assert is_relevant_file("frontend/app/page.tsx") is True
