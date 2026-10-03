# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_release_rebuild.py
"""Exercise the real release pipeline with complete portable Atlas sources."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread

import pytest

from tools.rebuild import PRODUCTS, copy_source, repository_files, reproduce, snapshot

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def release_baseline(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the complete actual release in an owned candidate tree."""
    root = tmp_path_factory.mktemp("atlas-release") / "source"
    copy_source(ROOT, root)
    env = {**os.environ, "SOURCE_DATE_EPOCH": "1790782681", "PYTHONDONTWRITEBYTECODE": "1"}
    for command in (
        ["node", "04_interactive_presentation/scripts/export_taxonomy.cjs"],
        [sys.executable, "04_interactive_presentation/scripts/build_datasets.py"],
        [sys.executable, "metadata/coverage_audit/build_coverage.py"],
        ["/usr/bin/bash", "metadata/build_inventory.sh"],
    ):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stderr.decode()
    # Only the provenance label was stale: actual record payloads remain exact.
    for product in PRODUCTS[:7]:
        assert (root / product).read_bytes() == (ROOT / product).read_bytes()
    return root


@pytest.fixture
def release_candidate(release_baseline: Path, tmp_path: Path) -> Path:
    """Copy a complete reviewed baseline before each negative mutation."""
    root = tmp_path / "candidate"
    shutil.copytree(release_baseline, root)
    return root


def test_real_release_api_creates_all_products_and_preserves_candidate(
    release_baseline: Path, tmp_path: Path
) -> None:
    before = snapshot(release_baseline)
    assert reproduce(release_baseline, tmp_path) == []
    assert snapshot(release_baseline) == before
    assert list(tmp_path.iterdir()) == []


def test_default_platform_workspace_reproduces_actual_release(release_baseline: Path) -> None:
    assert reproduce(release_baseline) == []


@pytest.mark.parametrize("product", PRODUCTS)
def test_each_missing_accepted_product_refuses_without_a_build(
    release_candidate: Path, tmp_path: Path, product: Path
) -> None:
    (release_candidate / product).unlink()
    before = snapshot(release_candidate)
    assert reproduce(release_candidate, tmp_path) == [
        f"reproducibility: missing accepted product {product}"
    ]
    assert snapshot(release_candidate) == before
    assert list(tmp_path.glob("atlas-rebuild-*")) == []


def test_corrupted_accepted_javascript_is_detected_by_real_export(
    release_candidate: Path, tmp_path: Path
) -> None:
    product = Path("04_interactive_presentation/data/taxonomy-audit.js")
    with (release_candidate / product).open("ab") as handle:
        handle.write(b"\n")
    before = snapshot(release_candidate)
    assert f"reproducibility: product changed {product}" in reproduce(release_candidate, tmp_path)
    assert snapshot(release_candidate) == before


def test_missing_real_node_exporter_fails_and_reports_every_uncreated_product(
    release_candidate: Path, tmp_path: Path
) -> None:
    (release_candidate / "04_interactive_presentation/scripts/export_taxonomy.cjs").unlink()
    failures = reproduce(release_candidate, tmp_path)
    assert "reproducibility: taxonomy exited 1" in failures
    assert all(f"reproducibility: product was not created {path}" in failures for path in PRODUCTS)


@pytest.mark.parametrize("receipt", ["", "Atlas\nGenerated (UTC): invalid\n"])
def test_invalid_actual_inventory_receipt_fails_closed(
    release_candidate: Path, tmp_path: Path, receipt: str
) -> None:
    (release_candidate / "metadata/validation_report.txt").write_text(receipt)
    assert reproduce(release_candidate, tmp_path) == [
        "reproducibility: source, workspace or build receipt cannot be read"
    ]


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_timeout_cannot_disable_process_bound(
    release_baseline: Path, tmp_path: Path, timeout: float
) -> None:
    assert reproduce(release_baseline, tmp_path, timeout=timeout) == [
        "reproducibility: timeout must be positive"
    ]


def test_real_node_timeout_cleans_only_owned_tree(release_baseline: Path, tmp_path: Path) -> None:
    before = snapshot(release_baseline)
    assert reproduce(release_baseline, tmp_path, timeout=1e-9) == [
        "reproducibility: builder timed out"
    ]
    assert snapshot(release_baseline) == before
    assert list(tmp_path.iterdir()) == []


def test_workspace_inside_candidate_is_refused(release_baseline: Path) -> None:
    assert reproduce(release_baseline, release_baseline / "metadata") == [
        "reproducibility: workspace must be outside the candidate"
    ]


def test_missing_workspace_and_missing_root_fail_closed(
    release_baseline: Path, tmp_path: Path
) -> None:
    message = ["reproducibility: source, workspace or build receipt cannot be read"]
    assert reproduce(release_baseline, tmp_path / "absent") == message
    assert reproduce(tmp_path / "absent", tmp_path) == message


def test_owned_symlink_is_refused_without_following_it(
    release_candidate: Path, tmp_path: Path
) -> None:
    (release_candidate / "README-alias.md").symlink_to(release_candidate / "README.md")
    assert reproduce(release_candidate, tmp_path) == [
        "reproducibility: source, workspace or build receipt cannot be read"
    ]


def test_walk_reports_unreadable_directory_and_prunes_private_environment_links(
    release_candidate: Path, tmp_path: Path
) -> None:
    with pytest.raises(OSError):
        list(repository_files(tmp_path / "absent"))
    (release_candidate / ".venv").symlink_to(tmp_path / "absent", target_is_directory=True)
    private = release_candidate / "docs/internal"
    private.mkdir(parents=True)
    (private / "not-public.md").write_text("Private continuity is not release content.\n")
    (release_candidate / ".coverage.test").write_bytes(b"coverage transient")
    assert not any(
        ".venv" in path.parts or "internal" in path.parts or path.name.startswith(".coverage")
        for path in repository_files(release_candidate)
    )
    assert reproduce(release_candidate, tmp_path) == []


def test_concurrent_candidate_and_stage_edits_are_detected(
    release_candidate: Path, tmp_path: Path
) -> None:
    events: list[str] = []

    def edit_after_real_coverage_report() -> None:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            stages = list(
                tmp_path.glob("atlas-rebuild-*/source/metadata/coverage_audit/COVERAGE.md")
            )
            if stages:
                stage = stages[0].parents[2]
                (stage / "README.md").write_text("Concurrent editorial update.\n")
                shutil.copy2(release_candidate / "README.md", stage / "additional-release-note.md")
                with (release_candidate / "README.md").open("a") as handle:
                    handle.write("\nConcurrent editorial update.\n")
                events.append("edited")
                return
            time.sleep(0.005)

    writer = Thread(target=edit_after_real_coverage_report)
    writer.start()
    try:
        failures = reproduce(release_candidate, tmp_path)
    finally:
        writer.join(timeout=65)
    assert not writer.is_alive()
    assert events == ["edited"]
    assert "reproducibility: candidate changed during verification" in failures
    assert "reproducibility: staged input changed README.md" in failures
    assert "reproducibility: undeclared build output additional-release-note.md" in failures


def test_native_inventory_honours_epoch_and_refuses_invalid_epoch(
    release_candidate: Path,
) -> None:
    before = snapshot(release_candidate)
    result = subprocess.run(
        ["/usr/bin/bash", "metadata/build_inventory.sh"],
        cwd=release_candidate,
        env={**os.environ, "SOURCE_DATE_EPOCH": "invalid"},
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert snapshot(release_candidate) == before
    result = subprocess.run(
        ["/usr/bin/bash", "metadata/build_inventory.sh"],
        cwd=release_candidate,
        env={**os.environ, "SOURCE_DATE_EPOCH": "1790782681"},
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert snapshot(release_candidate) == before


def test_named_pipe_is_refused_before_reading_source_bytes(
    release_candidate: Path, tmp_path: Path
) -> None:
    os.mkfifo(release_candidate / "unfinished-input.tsv")
    assert reproduce(release_candidate, tmp_path) == [
        "reproducibility: source, workspace or build receipt cannot be read"
    ]


def test_public_directory_named_internal_is_not_treated_as_private(
    release_candidate: Path,
) -> None:
    path = release_candidate / "metadata/internal/README.md"
    path.parent.mkdir()
    shutil.copy2(release_candidate / "README.md", path)
    assert path in set(repository_files(release_candidate))


def test_public_source_copy_preserves_catalogue_directories_and_refuses_symlinks(
    release_candidate: Path, tmp_path: Path
) -> None:
    source = tmp_path / "public-source-copy"
    copy_source(release_candidate, source)
    assert (source / "02_chemical_biochemical/01_ideal_flow_batch_cstr_pfr").is_dir()
    guide = Path("02_chemical_biochemical/01_ideal_flow_batch_cstr_pfr/README.md")
    assert (source / guide).read_bytes() == (release_candidate / guide).read_bytes()
    assert not any((source / product).exists() for product in PRODUCTS)
    (release_candidate / "README-alias.md").symlink_to(release_candidate / "README.md")
    with pytest.raises(OSError, match="symlink"):
        copy_source(release_candidate, tmp_path / "refused-source-copy")
