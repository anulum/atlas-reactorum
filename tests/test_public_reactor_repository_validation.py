# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — frozen public reactor-repository snapshot conformance

"""Exercise the released GitHub snapshot through its real optimized-safe validator."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/anulum_github/validate.py"
SNAPSHOT = SCRIPT.with_name("reactor_repositories.tsv")


def test_actual_public_repository_snapshot_stays_unchanged() -> None:
    """Validate the frozen 30-repository snapshot normally and under -O without changing its hash."""
    before = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
    for optimized in (False, True):
        result = run_cli(SCRIPT, optimize=optimized)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VALIDATION PASSED" in result.stdout and "records\t30" in result.stdout
    assert before == hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        ("name", "", "blank required"),
        ("description", "", "blank required"),
        ("evidence_boundary", "", "blank required"),
        ("category", "invented", "unknown repository category"),
        ("url", "https://example.org/project", "github.com"),
        ("url", "file://github.com/project", "HTTPS"),
        ("url", "https://[broken", "HTTPS"),
        ("url", "https://github.com.evil.test/project", "github.com"),
        ("source_url", "https://github.com/project", "api.github.com"),
        ("source_url", "http://api.github.com/repos", "HTTPS"),
        ("source_url", "https://[broken", "HTTPS"),
        ("archived", "True", "archived repository"),
        ("fork", "unknown", "invalid fork flag"),
        ("updated_at", "", "ISO timestamp"),
        ("updated_at", "yesterday", "ISO timestamp"),
        ("updated_at", "2026-09-27T12:00:00", "timezone"),
        ("retrieved", "2026", "full ISO date"),
        ("retrieved", "2026-02-30", "full ISO date"),
    ],
)
def test_snapshot_bad_metadata_refuses_under_optimization(
    tmp_path: Path, field: str, value: str, diagnostic: str
) -> None:
    """Reject altered metadata under -O with a specific diagnostic and unchanged input bytes."""
    fields, rows = read_table(SNAPSHOT)
    rows[0][field] = value
    path = tmp_path / "snapshot.tsv"
    write_table(path, fields, rows)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), optimize=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stderr and "Traceback" not in result.stderr
    assert "VALIDATION PASSED" not in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "corruption",
    [
        "count",
        "duplicate",
        "empty",
        "empty_file",
        "header",
        "truncated",
        "extra",
        "utf8",
        "quote",
        "missing",
    ],
)
def test_snapshot_identity_count_and_reads_refuse(tmp_path: Path, corruption: str) -> None:
    """Refuse damaged table structure, repository identity or the frozen snapshot count."""
    fields, rows = read_table(SNAPSHOT)
    if corruption == "count":
        rows.pop()
    elif corruption == "duplicate":
        rows[1] = rows[0].copy()
    elif corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    path = tmp_path / "snapshot.tsv"
    write_table(path, fields, rows)
    if corruption == "empty_file":
        path.write_bytes(b"")
    elif corruption == "truncated":
        path.write_text("\t".join(fields) + "\nonly-name\n")
    elif corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--input", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VALIDATION FAILED" in result.stderr and "Traceback" not in result.stderr
    if corruption == "count":
        assert "expected 30 rows" in result.stderr
    elif corruption == "duplicate":
        assert "duplicate repository name" in result.stderr


def test_public_repository_validator_api_and_entrypoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read the complete frozen snapshot through the public loader and run its validator entry point."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_public_repository_validator")
    assert module.load(SNAPSHOT) == read_table(SNAPSHOT)[1]
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    module.main()
