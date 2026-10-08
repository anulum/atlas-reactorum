# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_evidence_profile_validation.py

"""Exercise the whole original catalogue through the public profile API and CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread
from typing import cast

import pytest

from metadata.evidence_profiles.validate import (
    INPUTS,
    ProfileError,
    main,
    migrate_profiles,
    read_profile,
    validate_profiles,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "metadata/evidence_profiles/validate.py"
PROFILE = Path("metadata/evidence_profiles/profiles.json")
SNAPSHOT = hashlib.sha256((ROOT / INPUTS["taxonomy_sha256"]).read_bytes()).hexdigest()


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    """Copy every authentic profile input into a pytest-owned candidate.

    Parameters
    ----------
    tmp_path
        Temporary candidate root whose original readers remain production code.

    Returns
    -------
    pathlib.Path
        Root containing all bound input files and the complete profile document.
    """
    for relative in [*INPUTS.values(), str(PROFILE)]:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def document(root: Path) -> dict[str, object]:
    """Decode the candidate's complete profile document for explicit test mutations.

    Parameters
    ----------
    root
        Owned candidate root containing the profile file under its original name.

    Returns
    -------
    dict[str, object]
        Fresh mutable document; this helper performs no replacement validation.
    """
    value: dict[str, object] = json.loads((root / PROFILE).read_text())
    return value


def records(doc: dict[str, object]) -> list[dict[str, object]]:
    """Expose the existing mutable profile-record array without revalidation.

    Parameters
    ----------
    doc
        Decoded profile document from the original source fixture.

    Returns
    -------
    list[dict[str, object]]
        The same record array held by the document; edits remain in that candidate.
    """
    return cast(list[dict[str, object]], doc["records"])


def write(root: Path, doc: dict[str, object]) -> None:
    """Serialise an explicitly mutated profile document only in its owned candidate.

    Parameters
    ----------
    root
        Candidate root whose profile file is replaced; accepted inputs stay separate.
    doc
        Complete document to encode as UTF-8-compatible JSON with a final newline.
    """
    (root / PROFILE).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def refresh(root: Path, doc: dict[str, object], field: str) -> None:
    """Rebind one candidate digest after an explicit source mutation.

    Parameters
    ----------
    root
        Candidate root containing the mutated input under its original relative name.
    doc
        Profile document whose input-digest mapping is updated in place.
    field
        Existing INPUTS key identifying the source file to hash.

    Notes
    -----
    Digest rebinding does not approve the mutation. Original source readers still
    own semantic, locator, identity and review validation.
    """
    inputs = cast(dict[str, str], doc["inputs"])
    inputs[field] = hashlib.sha256((root / INPUTS[field]).read_bytes()).hexdigest()


def cli(
    root: Path, *args: str, optimize: bool = False, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the actual profile CLI against a complete candidate and bound snapshot.

    Parameters
    ----------
    root
        Candidate root passed through the public root option.
    args
        Additional public CLI options for migration, selection or refusal tests.
    optimize
        Whether to launch the selected Python with optimisation enabled.
    env
        Explicit child environment, or inherited selection when None.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Actual return code and decoded diagnostics, bounded by a 40-second timeout.
    """
    return subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimize else []),
            str(SCRIPT),
            "--root",
            str(root),
            "--snapshot",
            SNAPSHOT,
            *args,
        ],
        cwd=root.parent,
        capture_output=True,
        text=True,
        timeout=40,
        env=env,
    )


def test_whole_migration_and_explicit_reader_preserve_all_original_data(candidate: Path) -> None:
    """All 135 profiles preserve 599 claims, 148 source records, original values, ordering and frozen input bytes."""
    before = {relative: (candidate / relative).read_bytes() for relative in INPUTS.values()}
    doc = validate_profiles(candidate, SNAPSHOT)
    assert migrate_profiles(candidate, SNAPSHOT) == doc
    assert doc["record_count"] == 135
    original = json.loads((candidate / INPUTS["citations_sha256"]).read_text())
    assert doc["sources"] == original["sources"] and len(original["sources"]) == 148
    profiles = records(doc)
    assert sum(len(cast(list[object], row["claims"])) for row in profiles) == 599
    for index, profile in enumerate(profiles):
        legacy = original["records"][index]
        assert profile["entry_id"] == legacy["id"]
        assert profile["bound_values"] == legacy["values"]
        claims = cast(list[dict[str, object]], profile["claims"])
        assert [claim["citation"] for claim in claims] == legacy["citations"]
        assert cast(dict[str, object], profile["taxonomy_record"])["id"] == legacy["id"]
    for profile in (profiles[0], profiles[-1]):
        assert read_profile(candidate, SNAPSHOT, str(profile["entry_id"])) == profile
    assert {relative: (candidate / relative).read_bytes() for relative in INPUTS.values()} == before


def test_native_cli_migration_selection_and_optimized_refusal(candidate: Path) -> None:
    """Whole migration and selection agree; conflicting modes and forged review status refuse in both Python modes."""
    doc = document(candidate)
    for args in [(), ("--migrate",), ("--entry", "pwr")]:
        result = cli(candidate, *args)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == (records(doc)[0] if args == ("--entry", "pwr") else doc)
    assert main(["--root", str(candidate), "--snapshot", SNAPSHOT, "--entry", "absent"]) == 1
    result = cli(candidate, "--migrate", "--entry", "pwr")
    assert result.returncode == 1 and not result.stdout
    bad = records(doc)[-1]
    cast(dict[str, object], bad["review_disposition"])["complete_entry_review"] = True
    write(candidate, doc)
    for optimize in (False, True):
        result = cli(candidate, optimize=optimize)
        assert result.returncode == 1 and not result.stdout
        assert "schema validation failed" in result.stderr


@pytest.mark.parametrize(
    "mutation",
    [
        "last-id",
        "last-values",
        "last-kind",
        "last-mapping",
        "last-claim",
        "last-review",
        "last-temperature",
        "duplicate-parameter",
        "missing-last",
        "count",
        "source-hash",
        "unknown-capture",
        "new-independent-review",
    ],
)
def test_no_invalid_last_record_or_source_can_be_partially_read(
    candidate: Path, mutation: str
) -> None:
    """A defect in the last profile or source prevents even a valid first-entry read and emits no CLI payload."""
    doc = document(candidate)
    rows = records(doc)
    last = rows[-1]
    if mutation == "last-id":
        last["entry_id"] = rows[0]["entry_id"]
    elif mutation == "last-values":
        cast(dict[str, object], last["bound_values"])["principle"] = "Invented reactor claim"
    elif mutation == "last-kind":
        last["legacy_kind"] = "device"
    elif mutation == "last-mapping":
        cast(dict[str, object], last["entity_kind"])["category"] = "device"
    elif mutation == "last-claim":
        claims = cast(list[dict[str, object]], last["claims"])
        claims[0]["original_statement"] = "Invented source statement"
    elif mutation == "last-review":
        cast(dict[str, object], last["review_disposition"])["classification"] = {
            "state": "open",
            "basis": "legacy-kind-mapping",
            "questions": ["Changed", "Changed"],
        }
    elif mutation == "last-temperature":
        cast(list[dict[str, object]], last["parameters"])[0]["original_text"] = "Unknown"
    elif mutation == "duplicate-parameter":
        parameters = cast(list[object], last["parameters"])
        parameters.append(parameters[0])
    elif mutation == "missing-last":
        rows.pop()
    elif mutation == "count":
        doc["record_count"] = 136
    elif mutation == "source-hash":
        cast(list[dict[str, object]], doc["sources"])[-1]["sha256"] = "0" * 64
    elif mutation == "unknown-capture":
        source = next(
            item
            for item in cast(list[dict[str, object]], doc["sources"])
            if item["capture_method"] == "retained-source-review"
        )
        source["captured_at"] = "2026-10-03T00:00:00Z"
    else:
        cast(dict[str, object], last["review_disposition"])["independent_review"] = {
            "result": "approved"
        }
    write(candidate, doc)
    with pytest.raises(ProfileError):
        read_profile(candidate, SNAPSHOT, "pwr")
    result = cli(candidate)
    assert result.returncode == 1 and not result.stdout


@pytest.mark.parametrize("field", INPUTS)
def test_stale_input_and_explicit_snapshot_are_refused(candidate: Path, field: str) -> None:
    """Changed frozen input bytes and a mismatched requested taxonomy digest raise instead of accepting stale profiles."""
    with (candidate / INPUTS[field]).open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(ProfileError, match="hash is stale"):
        validate_profiles(candidate, SNAPSHOT)
    with pytest.raises(ProfileError, match="Requested taxonomy"):
        validate_profiles(ROOT, "0" * 64)


@pytest.mark.parametrize(
    "body",
    [
        b'{"schema_version":"1.0.0","schema_version":"1.0.0"}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e9999}',
        b"[]",
        b"not json",
        b"\xff",
    ],
)
def test_strict_json_refusal_never_echoes_source_input(candidate: Path, body: bytes) -> None:
    """Ambiguous, nonfinite or malformed profile JSON refuses without a traceback, source echo or candidate path."""
    (candidate / PROFILE).write_bytes(body)
    result = cli(candidate)
    assert result.returncode == 1 and not result.stdout
    assert "Traceback" not in result.stderr
    assert str(candidate) not in result.stderr


def test_unreadable_source_and_profile_are_refused(candidate: Path) -> None:
    """Missing frozen input and profile files yield their explicit public ProfileError refusals."""
    (candidate / INPUTS["audit_sha256"]).unlink()
    with pytest.raises(ProfileError, match="Frozen input"):
        validate_profiles(candidate, SNAPSHOT)
    (candidate / PROFILE).unlink()
    with pytest.raises(ProfileError, match="cannot be read"):
        validate_profiles(candidate, SNAPSHOT)


@pytest.mark.parametrize(
    "mutation", ["unknown-source", "outside-pdf", "bad-format", "whole-approval"]
)
def test_original_reader_still_owns_source_and_locator_validation(
    candidate: Path, mutation: str
) -> None:
    """Rebound candidate hashes cannot bypass original source, PDF locator, format or review validation."""
    doc = document(candidate)
    legacy_path = candidate / INPUTS["citations_sha256"]
    legacy = json.loads(legacy_path.read_text())
    claim = next(
        claim for row in legacy["records"] for claim in row["citations"] if claim["pdf_pages"]
    )
    if mutation == "unknown-source":
        claim["source_id"] = "missing"
    elif mutation == "outside-pdf":
        claim["pdf_pages"] = [999999]
    elif mutation == "bad-format":
        legacy["sources"][0]["format"] = "original-binary"
    else:
        legacy["records"][-1]["complete_entry_review"] = True
    legacy_path.write_text(json.dumps(legacy))
    refresh(candidate, doc, "citations_sha256")
    write(candidate, doc)
    with pytest.raises(ProfileError, match="Legacy citation validation"):
        validate_profiles(candidate, SNAPSHOT)


def test_duplicate_historical_identity_and_missing_native_reader_refuse(candidate: Path) -> None:
    """Duplicated audit identities refuse, and an unavailable real Node reader is a CLI failure."""
    doc = document(candidate)
    audit = candidate / INPUTS["audit_sha256"]
    with audit.open("a") as handle:
        handle.write(audit.read_text().splitlines()[1] + "\n")
    refresh(candidate, doc, "audit_sha256")
    write(candidate, doc)
    with pytest.raises(ProfileError, match="Historical audit identities"):
        validate_profiles(candidate, SNAPSHOT)
    result = cli(ROOT, env={**os.environ, "PATH": "/nonexistent-atlas-node"})
    assert result.returncode == 1 and "Native Node reader is unavailable" in result.stderr


def test_known_zero_requires_units_conditions_boundary_and_existing_claim(candidate: Path) -> None:
    """Metadata zero remains zero with explicit context; missing units or unknown original claim bindings refuse."""
    doc = document(candidate)
    row = records(doc)[0]
    claim = cast(list[dict[str, object]], row["claims"])[0]
    # This test supplies a metadata value to exercise zero preservation, not a
    # scientific assertion about PWR performance or a published catalogue edit.
    parameter = {
        "id": "test-value",
        "state": "known",
        "value": 0.0,
        "unit": "K",
        "conditions": "Explicit test conditions",
        "system_boundary": "Test boundary",
        "claim_ids": [claim["claim_id"]],
        "conversion_method": "Identity; no conversion",
        "original_text": claim["original_statement"],
    }
    row["parameters"] = [parameter]
    write(candidate, doc)
    selected = read_profile(candidate, SNAPSHOT, "pwr")
    assert cast(list[dict[str, object]], selected["parameters"])[0]["value"] == 0
    parameter["claim_ids"] = ["not-an-original-claim"]
    write(candidate, doc)
    with pytest.raises(ProfileError, match="unknown claim"):
        validate_profiles(candidate, SNAPSHOT)
    del parameter["unit"]
    write(candidate, doc)
    with pytest.raises(ProfileError, match="schema"):
        validate_profiles(candidate, SNAPSHOT)


def test_unknown_last_parent_refuses_whole_public_migration_and_reading(candidate: Path) -> None:
    """An unknown last-entry parent refuses API and optimised CLI reads while preserving all candidate inputs."""
    taxonomy = candidate / INPUTS["taxonomy_sha256"]
    with taxonomy.open("a") as handle:
        handle.write("window.REACTOR_TAXONOMY[134].parent_id='missing-parent';\n")
    snapshot = hashlib.sha256(taxonomy.read_bytes()).hexdigest()
    legacy_path = candidate / INPUTS["citations_sha256"]
    legacy = json.loads(legacy_path.read_text())
    legacy["taxonomy_sha256"] = snapshot
    legacy_path.write_text(json.dumps(legacy))
    doc = document(candidate)
    cast(dict[str, object], records(doc)[-1]["taxonomy_record"])["parent_id"] = "missing-parent"
    for field in INPUTS:
        refresh(candidate, doc, field)
    for profile in records(doc):
        review = cast(dict[str, object], profile["review_disposition"])
        cast(dict[str, object], review["source_inspection"])["source_snapshot_sha256"] = cast(
            dict[str, str], doc["inputs"]
        )["citations_sha256"]
    write(candidate, doc)
    before = {relative: (candidate / relative).read_bytes() for relative in INPUTS.values()}
    with pytest.raises(ProfileError, match="parent refers to an unknown entry"):
        migrate_profiles(candidate, snapshot)
    with pytest.raises(ProfileError, match="parent refers to an unknown entry"):
        read_profile(candidate, snapshot, "pwr")
    for args in [(), ("--migrate",), ("--entry", "pwr")]:
        result = cli(candidate, "--snapshot", snapshot, *args, optimize=True)
        assert result.returncode == 1 and not result.stdout
        assert "parent refers to an unknown entry" in result.stderr
        assert "Traceback" not in result.stderr and str(candidate) not in result.stderr
    assert {relative: (candidate / relative).read_bytes() for relative in INPUTS.values()} == before


def test_unknown_kind_refuses_both_validation_and_whole_migration(candidate: Path) -> None:
    """An undeclared entity kind refuses validation and migration even after source hashes are rebound."""
    taxonomy = candidate / INPUTS["taxonomy_sha256"]
    with taxonomy.open("a") as handle:
        handle.write("window.REACTOR_TAXONOMY[0].kind='unmapped entity';\n")
    legacy_path = candidate / INPUTS["citations_sha256"]
    legacy = json.loads(legacy_path.read_text())
    sha = hashlib.sha256(taxonomy.read_bytes()).hexdigest()
    legacy["taxonomy_sha256"] = sha
    legacy["records"][0]["values"]["kind"] = "unmapped entity"
    legacy_path.write_text(json.dumps(legacy))
    doc = document(candidate)
    for field in INPUTS:
        refresh(candidate, doc, field)
    with pytest.raises(ProfileError, match="no declared entity"):
        validate_profiles(candidate, sha, doc)
    with pytest.raises(ProfileError, match="no declared entity"):
        migrate_profiles(candidate, sha)


def test_historical_structure_and_original_context_cannot_be_rewritten(candidate: Path) -> None:
    """Altered taxonomy context, audit columns or missing legacy inputs cannot be accepted as the original snapshot."""
    doc = document(candidate)
    cast(dict[str, object], records(doc)[-1]["taxonomy_record"])["mode"] = "Invented mode"
    with pytest.raises(ProfileError, match="taxonomy context"):
        validate_profiles(candidate, SNAPSHOT, doc)
    audit = candidate / INPUTS["audit_sha256"]
    audit.write_text(audit.read_text().replace("id\tname", "entry\tname", 1))
    doc = document(candidate)
    refresh(candidate, doc, "audit_sha256")
    with pytest.raises(ProfileError, match="Historical audit structure"):
        validate_profiles(candidate, SNAPSHOT, doc)
    (candidate / INPUTS["audit_sha256"]).unlink()
    with pytest.raises(ProfileError, match="Legacy inputs"):
        migrate_profiles(candidate, SNAPSHOT)


def test_native_legacy_process_timeout_is_safely_refused(candidate: Path) -> None:
    """An actual nonterminating taxonomy child is bounded and reported as a public legacy-input refusal."""
    taxonomy = candidate / INPUTS["taxonomy_sha256"]
    with taxonomy.open("a") as handle:
        handle.write("while(true){}\n")
    legacy_path = candidate / INPUTS["citations_sha256"]
    legacy = json.loads(legacy_path.read_text())
    legacy["taxonomy_sha256"] = hashlib.sha256(taxonomy.read_bytes()).hexdigest()
    legacy_path.write_text(json.dumps(legacy))
    with pytest.raises(ProfileError, match="Legacy inputs"):
        migrate_profiles(candidate, legacy["taxonomy_sha256"])


def test_concurrent_frozen_input_edit_cannot_return_a_mixed_snapshot(candidate: Path) -> None:
    """A source edit after the real Node child launches refuses a mixed snapshot and reaps the editor thread."""
    taxonomy = candidate / INPUTS["taxonomy_sha256"]
    with taxonomy.open("a") as handle:
        handle.write("Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,1200);\n")
    legacy_path = candidate / INPUTS["citations_sha256"]
    legacy = json.loads(legacy_path.read_text())
    sha = hashlib.sha256(taxonomy.read_bytes()).hexdigest()
    legacy["taxonomy_sha256"] = sha
    legacy_path.write_text(json.dumps(legacy))
    doc = migrate_profiles(candidate, sha)
    changed: list[bool] = []
    children = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    previous_children = set(children.read_text().split())
    node = shutil.which("node")
    assert node is not None

    def edit_audit() -> None:
        # Mutate only after this validation's real Node child has launched.
        """Wait for this validation's real Node child, then record one owned audit mutation."""
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            for pid in set(children.read_text().split()) - previous_children:
                try:
                    arguments = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
                except FileNotFoundError:
                    continue
                if arguments[0] == os.fsencode(node) and os.fsencode(candidate) in arguments:
                    with (candidate / INPUTS["audit_sha256"]).open("a") as handle:
                        handle.write("\n")
                    changed.append(True)
                    return
            time.sleep(0.01)

    editor = Thread(target=edit_audit)
    editor.start()
    try:
        with pytest.raises(ProfileError, match="changed during validation"):
            validate_profiles(candidate, sha, doc)
    finally:
        editor.join(timeout=35)
    assert changed == [True] and not editor.is_alive()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10**400])
def test_in_memory_numeric_input_obeys_the_same_finite_value_contract(
    candidate: Path, value: float | int
) -> None:
    """Nonfinite or unrepresentably large in-memory values refuse under the original finite-parameter contract."""
    doc = document(candidate)
    row = records(doc)[0]
    claim = cast(list[dict[str, object]], row["claims"])[0]
    row["parameters"] = [
        {
            "id": "test-value",
            "state": "known",
            "value": value,
            "unit": "K",
            "conditions": "Test conditions",
            "system_boundary": "Test boundary",
            "claim_ids": [claim["claim_id"]],
            "conversion_method": "Identity",
            "original_text": claim["original_statement"],
        }
    ]
    with pytest.raises(ProfileError, match="finite representable"):
        validate_profiles(candidate, SNAPSHOT, doc)
