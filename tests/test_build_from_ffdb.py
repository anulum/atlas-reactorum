# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB pinned producer CLI tests

"""Run the actual pinned producer, including normal and optimised refusal surfaces."""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from ._catalogue_inputs import run_cli
from .conftest import ROOT

LAYER = ROOT / "05_global_reactor_map/imports/fusion/ffdb"
SCRIPT = LAYER / "build_from_ffdb.py"
CAPTURE = ROOT / "tests/data/fusion_ffdb/visible_data.frames"


@pytest.fixture
def producer() -> ModuleType:
    """Load the actual pinned producer's public command implementation.

    Returns
    -------
    types.ModuleType
        Standalone FFDB producer with its normal source-validation imports.
    """
    return importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.build_from_ffdb")


@pytest.mark.parametrize("optimize", [False, True])
def test_real_cli_reproduces_both_source_bound_products(tmp_path: Path, optimize: bool) -> None:
    """Reproduce both registered products twice through normal and optimised native CLI runs.

    All 174 identities and 137 map points remain present, and source-bound
    product bytes agree with the checkout without promoting scientific approval.
    """
    output = tmp_path / "first"
    result = run_cli(SCRIPT, "--output", str(output), optimize=optimize)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["table_records"] == 174
    assert summary["map_records"] == 137
    assert summary["scientific_approval"] is False
    with (output / "fusion_facilities.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 174
    assert sum(bool(row["lat"]) for row in rows) == 137
    second = tmp_path / "second"
    repeat = run_cli(SCRIPT, "--output", str(second), optimize=optimize)
    assert repeat.returncode == 0, repeat.stderr
    for name in ["fusion_facilities.tsv", "field_provenance.json"]:
        assert (output / name).read_bytes() == (second / name).read_bytes()
        assert (output / name).read_bytes() == (LAYER / name).read_bytes()


@pytest.mark.parametrize("optimize", [False, True])
def test_real_cli_refuses_changed_source_without_creating_output(
    tmp_path: Path, optimize: bool
) -> None:
    """Refuse changed capture bytes before creating the requested output directory."""
    source = tmp_path / "changed.raw"
    source.write_bytes(CAPTURE.read_bytes() + b" ")
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--source", str(source), "--output", str(output), optimize=optimize)
    assert result.returncode == 2
    assert result.stderr == "FFDB source does not match its registered SHA-256.\n"
    assert not output.exists()


@pytest.mark.parametrize("optimize", [False, True])
def test_real_cli_refuses_integer_decoder_limit_without_output_or_traceback(
    tmp_path: Path, optimize: bool
) -> None:
    """Convert oversized-integer decoding failure into a bounded CLI refusal without output."""
    first = '{"oversized_integer":' + "1" * 5000 + "}"
    payload = f"{len(first)};{first}2;{{}}".encode()
    source = tmp_path / "oversized_integer.frames"
    source.write_bytes(payload)
    registry = json.loads((LAYER / "source_manifest.json").read_text())
    registry["artifact_sha256"] = hashlib.sha256(payload).hexdigest()
    registry["artifact_bytes"] = len(payload)
    manifest = tmp_path / "source.json"
    manifest.write_text(json.dumps(registry), encoding="utf-8")
    output = tmp_path / "never_created"
    result = run_cli(
        SCRIPT,
        "--source",
        str(source),
        "--manifest",
        str(manifest),
        "--output",
        str(output),
        optimize=optimize,
    )
    assert result.returncode == 2
    assert result.stderr == "FFDB source contains invalid JSON.\n"
    assert not output.exists()


@pytest.mark.parametrize("optimize", [False, True])
def test_real_cli_preserves_existing_directory(tmp_path: Path, optimize: bool) -> None:
    """Preserve an existing directory's sentinel and refuse creating source products within it."""
    sentinel = tmp_path / "original.txt"
    sentinel.write_text("owner original", encoding="utf-8")
    result = run_cli(SCRIPT, "--output", str(tmp_path), optimize=optimize)
    assert result.returncode == 2
    assert result.stderr == "FFDB output cannot be created in a new directory.\n"
    assert sentinel.read_text() == "owner original"
    assert not (tmp_path / "fusion_facilities.tsv").exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 3),
        ("schema_version", True),
        ("schema_version", 2.0),
        ("source_url", "https://example.org/private"),
        ("artifact_sha256", "not-a-digest"),
        ("original_response_sha256", "not-a-digest"),
        ("artifact_kind", "publisher-viewer-response"),
        ("retrieved_date", "20261002"),
    ],
)
def test_real_cli_refuses_invalid_registry(tmp_path: Path, field: str, value: object) -> None:
    """Reject malformed source identity and registry fields without leaking URLs or tracebacks."""
    registry = json.loads((LAYER / "source_manifest.json").read_text())
    registry[field] = value
    manifest = tmp_path / "source.json"
    manifest.write_text(json.dumps(registry), encoding="utf-8")
    result = run_cli(SCRIPT, "--manifest", str(manifest))
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "example.org" not in result.stderr


@pytest.mark.parametrize("body", [b"{", b"\xff"])
def test_real_cli_refuses_malformed_registry(tmp_path: Path, body: bytes) -> None:
    """Report invalid JSON or UTF-8 in the registry through the producer's public CLI error."""
    manifest = tmp_path / "source.json"
    manifest.write_bytes(body)
    result = run_cli(SCRIPT, "--manifest", str(manifest))
    assert result.returncode == 2
    assert result.stderr == "FFDB source registry cannot be read as valid JSON.\n"


def test_producer_api_checks_pinned_inputs_before_writing(
    producer: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """Bind a successful producer API summary to the actual capture's SHA-256 digest."""
    assert producer.main([]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["source_sha256"] == hashlib.sha256(CAPTURE.read_bytes()).hexdigest()


@pytest.mark.parametrize("change", ["kind", "original", "date"])
def test_real_cli_refuses_registry_and_artifact_acquisition_disagreement(
    tmp_path: Path, change: str
) -> None:
    """Refuse mismatched acquisition metadata even when the altered artifact digest is repinned."""
    from .test_ffdb_reader import captured_frames, framed

    registry = json.loads((LAYER / "source_manifest.json").read_text())
    frames = captured_frames()
    projection = cast(dict[str, object], frames[0]["atlas_projection"])
    if change == "kind":
        frames[0] = {}
    elif change == "original":
        projection["original_response_sha256"] = "0" * 64
    else:
        projection["retrieved_date"] = "2026-10-03"
    payload = framed(frames)
    source = tmp_path / "visible_data.frames"
    source.write_bytes(payload)
    registry["artifact_sha256"] = hashlib.sha256(payload).hexdigest()
    manifest = tmp_path / "source.json"
    manifest.write_text(json.dumps(registry))
    output = tmp_path / "never_created"
    result = run_cli(
        SCRIPT, "--source", str(source), "--manifest", str(manifest), "--output", str(output)
    )
    assert result.returncode == 2
    assert result.stderr == "FFDB selection differs from its registered acquisition identity.\n"
    assert not output.exists()
