# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_preflight.py
"""Run repository checks through their public functions and native CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.preflight import check_docs, check_headers, check_reproducibility, check_secrets, main
from tools.rebuild import snapshot

from .test_release_rebuild import release_baseline as release_baseline
from .test_release_rebuild import release_candidate as release_candidate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/preflight.py"


def test_public_reproducibility_wrapper_preserves_actual_candidate(
    release_baseline: Path, tmp_path: Path
) -> None:
    """Rebuild the full frozen release without changing any accepted candidate byte."""
    before = snapshot(release_baseline)
    assert check_reproducibility(release_baseline, tmp_path) == []
    assert snapshot(release_baseline) == before


def test_public_header_and_documentation_defaults_check_actual_checkout() -> None:
    """Resolve default-root links and legal headers against the complete actual checkout."""
    assert check_docs() == []
    assert check_headers() == []


@pytest.mark.parametrize("optimised", [False, True])
def test_native_all_checks_resolve_imports_from_another_directory(
    release_baseline: Path, tmp_path: Path, optimised: bool
) -> None:
    """Run all CLI checks outside the checkout, with assertions also disabled in the -O case.

    The complete baseline must remain unchanged and each native check must
    report success; resolving imports alone is insufficient.
    """
    before = snapshot(release_baseline)
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimised else []),
            str(SCRIPT),
            "--root",
            str(release_baseline),
            "--workspace",
            str(tmp_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{name:16s} ok" for name in ("docs", "headers", "reproducibility", "secrets")
    ]
    assert snapshot(release_baseline) == before


def test_public_main_runs_selected_checks_and_reports_failures(
    release_candidate: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report missing and escaping documentation links while retaining the header result."""
    doc = release_candidate / "05_global_reactor_map/imports/fusion/README.md"
    with doc.open("a") as handle:
        handle.write(
            "\n[Missing](missing-reference.md#section)\n[Outside](../../../../../../private.md)\n"
        )
    assert main(["--root", str(release_candidate), "--check", "docs", "--check", "headers"]) == 1
    output = capsys.readouterr().out
    assert "docs             FAIL" in output
    assert "headers          ok" in output
    assert "fusion/README.md cites a missing candidate path" in output


def test_url_encoded_and_angled_relative_links_resolve_actual_files(
    release_candidate: Path,
) -> None:
    """Accept existing encoded and angled local links alongside fragments and remote links."""
    with (release_candidate / "README.md").open("a") as handle:
        handle.write(
            "\n[Schema](04_interactive_presentation/data/global_reactors.schema.json#properties)\n"
        )
        handle.write('[Encoded](04_interactive_presentation/data/%52EADME.md "dataset notes")\n')
        handle.write("[Angle](<04_interactive_presentation/data/README.md>)\n")
        handle.write(
            "[Fragment](#atlas) [Mail](mailto:protoscience@anulum.li) [Remote](//www.anulum.li)\n"
        )
    assert check_docs(release_candidate) == []


@pytest.mark.parametrize("check", ["docs", "headers", "secrets"])
def test_native_unreadable_owned_file_fails_without_echoing_contents(
    release_candidate: Path, tmp_path: Path, check: str
) -> None:
    """Reject a dangling source symlink without exposing its target or filesystem exception."""
    target = release_candidate / "README.md"
    target.rename(tmp_path / "readme")
    target.symlink_to(tmp_path / "absent")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(release_candidate), "--check", check],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 1
    assert f"{check}: candidate files cannot be read" in result.stdout
    assert result.stderr == ""
    assert str(tmp_path) not in result.stdout


def test_native_malformed_markdown_encoding_fails_closed(release_candidate: Path) -> None:
    """Refuse non-UTF-8 public Markdown through the real CLI's sanitised failure route."""
    target = release_candidate / "README.md"
    target.write_bytes(target.read_bytes() + b"\xff")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(release_candidate), "--check", "docs"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 1
    assert "docs: candidate files cannot be read" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize("shape", ["assignment", "private", "aws"])
def test_benign_credential_shapes_are_reported_without_value_disclosure(
    release_candidate: Path, shape: str
) -> None:
    """Detect three inert credential-shaped strings without including their values in reports."""
    value = "review-fixture-never-a-credential"
    examples = {
        "assignment": "api" + "_key = '" + value + "'",
        "private": "-----BEGIN " + "RSA " + "PRIVATE" + " KEY-----",
        "aws": "aws_" + "secret_access_key = " + value,
    }
    with (release_candidate / "README.md").open("a") as handle:
        handle.write("\n" + examples[shape] + "\n")
    failures = check_secrets(release_candidate)
    assert len(failures) == 1
    assert failures[0].startswith("secrets: README.md matches ")
    assert value not in failures[0]


def test_binary_asset_is_not_decoded_as_text(release_candidate: Path) -> None:
    """Keep an actual PNG acceptable when its copied filename lacks a recognised asset suffix."""
    asset = next(release_candidate.rglob("*.png"))
    shutil.copy2(asset, release_candidate / "opaque-asset.bin")
    assert check_secrets(release_candidate) == []


@pytest.mark.parametrize("mutation", ["empty", "short", "spdx", "contact", "module"])
def test_every_branding_header_line_is_required(release_candidate: Path, mutation: str) -> None:
    """Refuse missing, truncated or displaced ownership fields on the actual preflight script."""
    target = release_candidate / "tools/preflight.py"
    lines = target.read_text().splitlines()
    if mutation == "empty":
        lines = []
    elif mutation == "short":
        lines = lines[1:7]
    elif mutation == "spdx":
        lines[1] = "# SPDX marker elsewhere is insufficient"
    elif mutation == "contact":
        lines[6] = "# Contact absent"
    else:
        lines[7] = "# Module label absent"
    target.write_text("\n".join(lines) + "\n")
    assert check_headers(release_candidate) == [
        "headers: tools/preflight.py lacks the seven-line header"
    ]


def test_argparse_rejects_unknown_check_before_work(release_baseline: Path) -> None:
    """Refuse an unsupported CLI check with argparse's usage status before verification."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(release_baseline), "--check", "missing"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_environment_temporary_directory_inside_candidate_is_refused(
    release_candidate: Path,
) -> None:
    """Refuse TMPDIR within the accepted candidate without changing its complete snapshot."""
    before = snapshot(release_candidate)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(release_candidate),
            "--check",
            "reproducibility",
        ],
        env={**os.environ, "TMPDIR": str(release_candidate)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 1
    assert "workspace must be outside the candidate" in result.stdout
    assert snapshot(release_candidate) == before


def test_malformed_owned_source_cannot_pass_credential_scan(release_candidate: Path) -> None:
    """Treat invalid UTF-8 in an owned Markdown file as a scan failure rather than binary data."""
    target = release_candidate / "README.md"
    target.write_bytes(target.read_bytes() + b"\xff")
    assert check_secrets(release_candidate) == ["secrets: README.md is not UTF-8 text"]
