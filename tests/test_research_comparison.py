# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — real research comparison API and CLI tests
"""Exercise native restoration with the whole original catalogue and exported example."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

import pytest

from tools.research_comparison import ComparisonError, main, restore_comparison

from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/research"
MANIFEST = cast(dict[str, str], json.loads((EXAMPLE / "comparison-manifest.json").read_text()))
BUNDLE = EXAMPLE / "pwr-bwr-comparison.json"


def test_original_api_restores_both_profiles_claims_sources_and_missing_values() -> None:
    """Restore the exact accepted PWR/BWR comparison with non-comparable parameters and incomplete reviews intact."""
    restored = restore_comparison(
        ROOT, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"]
    )
    original = json.loads(BUNDLE.read_text())
    assert restored == original
    assert original["selection"]["entry_ids"] == ["pwr", "bwr"]
    assert original["parameter_comparisons"][0]["state"] == "not_comparable"
    assert all(not p["review_disposition"]["complete_entry_review"] for p in original["profiles"])
    assert (
        restore_comparison(ROOT, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])
        == restored
    )


@pytest.mark.parametrize("selection", [None, ""])
def test_actual_python_api_selects_its_interpreter_when_path_has_only_node(
    monkeypatch: pytest.MonkeyPatch, selection: str | None
) -> None:
    """Restore through the real Node/Python chain with no Python executable on PATH."""
    node = shutil.which("node")
    assert node is not None
    monkeypatch.setenv("PATH", str(Path(node).parent))
    if selection is None:
        monkeypatch.delenv("ATLAS_PYTHON", raising=False)
    else:
        monkeypatch.setenv("ATLAS_PYTHON", selection)
    assert shutil.which("python3") is None
    restored = restore_comparison(
        ROOT, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"]
    )
    assert restored == json.loads(BUNDLE.read_text())


def test_actual_explicit_unavailable_python_selection_refuses_without_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """Refuse an actual unavailable configured checker while preserving original custody."""
    before = BUNDLE.read_bytes()
    monkeypatch.setenv("ATLAS_PYTHON", str(tmp_path / "absent-native-python"))
    with pytest.raises(ComparisonError, match="source binding"):
        restore_comparison(ROOT, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])
    captured = capfd.readouterr()
    assert captured.out == "" and captured.err == ""
    assert BUNDLE.read_bytes() == before


@pytest.mark.parametrize(
    "snapshot,digest", [("x", "a" * 64), ("a" * 64, "x"), ("A" * 64, "a" * 64)]
)
def test_api_refuses_invalid_explicit_hashes(snapshot: str, digest: str) -> None:
    """Reject malformed or uppercase explicit snapshot and bundle digests."""
    with pytest.raises(ComparisonError, match="Explicit lowercase"):
        restore_comparison(ROOT, BUNDLE, snapshot, digest)


def test_api_refuses_changed_bundle_bytes(tmp_path: Path) -> None:
    """Reject comparison byte drift against its explicit accepted bundle digest."""
    changed = tmp_path / "comparison.json"
    changed.write_bytes(BUNDLE.read_bytes() + b" ")
    with pytest.raises(ComparisonError, match="file digest"):
        restore_comparison(ROOT, changed, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])


def test_api_refuses_new_digest_for_changed_original_claim(tmp_path: Path) -> None:
    """Reject changed original claim text even when the comparison digest is updated."""
    original = json.loads(BUNDLE.read_text())
    original["profiles"][0]["claims"][0]["original_statement"] += " unsupported changed text"
    data = (json.dumps(original, ensure_ascii=False, indent=2) + "\n").encode()
    changed = tmp_path / "comparison.json"
    changed.write_bytes(data)
    with pytest.raises(ComparisonError, match="source binding"):
        restore_comparison(
            ROOT, changed, MANIFEST["profile_sha256"], hashlib.sha256(data).hexdigest()
        )


def test_api_refuses_unavailable_native_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse restoration when the required native Node comparison reader is unavailable."""
    monkeypatch.setenv("PATH", "")
    with pytest.raises(ComparisonError, match="Node comparison reader"):
        restore_comparison(ROOT, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])


def test_api_refuses_unreadable_bundle_and_missing_original_snapshot(tmp_path: Path) -> None:
    """Reject an unreadable comparison or absent complete original snapshot."""
    for root, file in [(ROOT, tmp_path / "missing.json"), (tmp_path, BUNDLE)]:
        with pytest.raises(ComparisonError, match="unavailable"):
            restore_comparison(root, file, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])


def test_whole_original_validation_checks_unselected_last_profile(tmp_path: Path) -> None:
    """Reject changed unselected profile facts through whole original-snapshot validation."""
    for relative in [
        "metadata/evidence_profiles/profiles.json",
        "04_interactive_presentation/data/taxonomy-expanded.js",
        "metadata/taxonomy_audit/claim_citations.json",
        "metadata/taxonomy_audit/audit.tsv",
    ]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    file = tmp_path / "metadata/evidence_profiles/profiles.json"
    profiles = json.loads(file.read_text())
    profiles["records"][-1]["taxonomy_record"]["name"] += " unsupported change"
    file.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n")
    with pytest.raises(ComparisonError, match="unavailable"):
        restore_comparison(tmp_path, BUNDLE, MANIFEST["profile_sha256"], MANIFEST["bundle_sha256"])


def test_public_main_restores_original_canonical_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Restore exact accepted comparison JSON through public main without stderr output."""
    assert (
        main(
            [
                "--root",
                str(ROOT),
                "--bundle",
                str(BUNDLE),
                "--snapshot",
                MANIFEST["profile_sha256"],
                "--bundle-sha256",
                MANIFEST["bundle_sha256"],
            ]
        )
        == 0
    )
    result = capsys.readouterr()
    assert json.loads(result.out) == json.loads(BUNDLE.read_text())
    assert result.err == ""


@pytest.mark.parametrize("snapshot", ["0" * 64, "invalid"])
def test_real_public_cli_refuses_snapshot_with_fixed_stderr(snapshot: str) -> None:
    """Refuse invalid or mismatched snapshots with the exact bounded public CLI diagnostic."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.research_comparison",
            "--root",
            str(ROOT),
            "--bundle",
            str(BUNDLE),
            "--snapshot",
            snapshot,
            "--bundle-sha256",
            MANIFEST["bundle_sha256"],
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "research comparison: input or source binding refused\n"


def test_real_public_cli_restores_original_export() -> None:
    """Restore the original exported comparison through the actual Python module CLI."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.research_comparison",
            "--root",
            str(ROOT),
            "--bundle",
            str(BUNDLE),
            "--snapshot",
            MANIFEST["profile_sha256"],
            "--bundle-sha256",
            MANIFEST["bundle_sha256"],
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == json.loads(BUNDLE.read_text())


def test_actual_browser_download_restores_original_research_comparison(
    browser: Browser, tmp_path: Path
) -> None:
    """Download the real browser comparison with the accepted digest and restore its exact original content."""
    browser.command(
        "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp_path)}
    )
    browser.evaluate("""
      const first = document.querySelector('#compareA');
      const second = document.querySelector('#compareB');
      first.value = 'pwr'; second.value = 'bwr'; document.querySelector('#compareC').value = '';
      second.dispatchEvent(new Event('change', {bubbles:true}));
    """)
    deadline = time.monotonic() + 15
    while (
        browser.evaluate(
            "document.querySelector('#compareStatus').textContent.startsWith('Comparison ready.')"
        )
        is not True
    ):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    browser.evaluate("document.querySelector('#compareDownload').click()")
    deadline = time.monotonic() + 15
    while not list(tmp_path.glob("*.json")):
        assert time.monotonic() < deadline
        time.sleep(0.05)
    downloaded = next(tmp_path.glob("*.json"))
    digest = hashlib.sha256(downloaded.read_bytes()).hexdigest()
    assert digest == MANIFEST["bundle_sha256"]
    restored = restore_comparison(ROOT, downloaded, MANIFEST["profile_sha256"], digest)
    assert restored == json.loads(BUNDLE.read_text())
