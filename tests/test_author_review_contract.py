# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_author_review_contract.py

"""Admit complete actual source assessments through the public Python API and CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
from coverage import Coverage

from metadata.evidence_profiles.review_contract import ReviewError, validate_author_reviews
from metadata.evidence_profiles.validate import INPUTS

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "metadata/evidence_profiles/review_contract.py"
PROFILE = Path("metadata/evidence_profiles/profiles.json")
REVIEW = Path("metadata/evidence_profiles/author_reviews.json")
SNAPSHOT = hashlib.sha256((ROOT / INPUTS["taxonomy_sha256"]).read_bytes()).hexdigest()


def run_owner_cli(args: list[str], owner: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Measure an exact source-copy CLI when its parent collects coverage.

    Parameters
    ----------
    args : list of str
        Real interpreter, owning script and complete public CLI arguments.
    owner : pathlib.Path
        Tree containing the byte-verified Python modules and damaged schema.
    cwd : pathlib.Path
        Working directory for the isolated native process.

    Returns
    -------
    subprocess.CompletedProcess
        Actual CLI output and status, with subprocess measurements retained
        in the active parent's data allocation when coverage is enabled.
    """
    environment = os.environ.copy()
    active = Coverage.current()
    if active is not None:
        environment["COVERAGE_FILE"] = str(
            Path(cast(str, active.get_option("run:data_file"))).resolve()
        )
        args = [
            args[0],
            "-m",
            "coverage",
            "run",
            "--rcfile",
            str(ROOT / "pyproject.toml"),
            "--source",
            str(owner / "metadata/evidence_profiles"),
            *args[1:],
        ]
    return subprocess.run(
        args, cwd=cwd, env=environment, capture_output=True, text=True, timeout=65
    )


def read(path: Path) -> dict[str, object]:
    """Read a complete authentic or explicitly mutated owned JSON input.

    Parameters
    ----------
    path : pathlib.Path
        Whole input retained under its actual source or candidate path.

    Returns
    -------
    dict of str to object
        Mutable original document, without replacement validation.
    """
    value: object = json.loads(path.read_text())
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def records(doc: dict[str, object]) -> list[dict[str, object]]:
    """Expose the source document's actual mutable record array.

    Parameters
    ----------
    doc : dict of str to object
        Original document or a test-owned explicitly altered copy.

    Returns
    -------
    list of dict
        Original array; the production validator owns its semantic admission.
    """
    return cast(list[dict[str, object]], doc["records"])


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    """Retain actual all135 assessment and source-bound original inputs in an owned tree.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-owned Samsung allocation for this individual native refusal case.

    Returns
    -------
    pathlib.Path
        Complete original inputs plus the genuine author-assessment input.
    """
    source = Path(os.environ.get("ATLAS_AUTHOR_REVIEW_INPUT", str(ROOT / REVIEW)))
    assert source.is_file(), "Complete actual author-review input is required"
    for relative in [*INPUTS.values(), str(PROFILE)]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    shutil.copy2(source, tmp_path / REVIEW)
    return tmp_path


def test_all135_original_values_claims_sources_and_unknown_activity_survive(
    candidate: Path,
) -> None:
    """Preserve every original value and source input through whole-catalogue admission.

    Parameters
    ----------
    candidate : pathlib.Path
        Actual source assessment and complete original production inputs.
    """
    before = {
        name: (candidate / name).read_bytes()
        for name in [*INPUTS.values(), str(PROFILE), str(REVIEW)]
    }
    result = validate_author_reviews(candidate, SNAPSHOT)
    baseline = read(candidate / PROFILE)
    assert len(records(result)) == 135
    assert sum(len(cast(dict[str, object], row["fields"])) for row in records(result)) == 2835
    for review, original in zip(records(result), records(baseline), strict=True):
        assert review["entry_id"] == original["entry_id"]
        fields = cast(dict[str, dict[str, object]], review["fields"])
        assert {name: field["original_value"] for name, field in fields.items()} == original[
            "taxonomy_record"
        ]
        assert review["current_activity"] == "unknown"
        assert review["complete_entry_review"] is True
        assert review["review_scope"] == "all-original-fields-and-selected-sources"
        assert review["review_basis"] == "author-source-inspection"
        assert review["independent_review"] is None
    assert {name: (candidate / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("explicit_input", [False, True])
def test_real_cli_returns_the_same_complete_input(
    candidate: Path, optimized: bool, explicit_input: bool
) -> None:
    """Use the actual CLI in normal and optimized interpreter modes without input mutation.

    Parameters
    ----------
    candidate : pathlib.Path
        Complete actual all135 source assessment and original inputs.
    optimized : bool
        Whether the actual child interpreter runs with Python optimization enabled.
    explicit_input : bool
        Whether the CLI receives its input path or uses the retained default input.
    """
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimized else []),
            str(SCRIPT),
            "--root",
            str(candidate),
            "--snapshot",
            SNAPSHOT,
            *(["--reviews", str(candidate / REVIEW)] if explicit_input else []),
        ],
        cwd=candidate.parent,
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == read(candidate / REVIEW)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-entry",
        "reordered-entry",
        "changed-value",
        "unknown-claim",
        "unknown-source",
        "missing-claim-source",
        "unbound-science",
        "scientific-editorial",
        "false-score",
        "changed-input",
        "incomplete-entry",
        "review-scope",
        "review-basis",
        "independent-acceptance",
        "past-review",
    ],
)
def test_full_record_and_field_binding_refuses(candidate: Path, mutation: str) -> None:
    """Reject concrete corruptions of the actual full source assessment.

    Parameters
    ----------
    candidate : pathlib.Path
        Complete actual inputs whose accepted source bytes remain unchanged.
    mutation : str
        Named corruption applied only to this owned in-memory document.
    """
    doc = read(candidate / REVIEW)
    items = records(doc)
    fields = cast(dict[str, dict[str, object]], items[0]["fields"])
    if mutation == "missing-entry":
        items.pop()
    elif mutation == "reordered-entry":
        items[0], items[1] = items[1], items[0]
    elif mutation == "changed-value":
        fields["principle"]["original_value"] = "changed original statement"
    elif mutation == "unknown-claim":
        fields["principle"]["claim_ids"] = ["absent:principle:1"]
    elif mutation == "unknown-source":
        fields["principle"]["source_ids"] = ["absent-source"]
    elif mutation == "missing-claim-source":
        fields["principle"]["source_ids"] = []
    elif mutation == "unbound-science":
        fields["principle"]["source_ids"] = []
        fields["principle"]["claim_ids"] = []
    elif mutation == "scientific-editorial":
        fields["principle"]["disposition"] = "editorial"
    elif mutation == "false-score":
        fields["principle"]["disposition"] = "unscored"
    elif mutation == "changed-input":
        cast(dict[str, object], doc["baseline_inputs"])["taxonomy_sha256"] = "0" * 64
    elif mutation == "past-review":
        doc["reviewed_on"] = "2000-01-01"
    elif mutation == "review-scope":
        items[0]["review_scope"] = "independently-qualified-hardware"
    elif mutation == "review-basis":
        items[0]["review_basis"] = "independent-review"
    elif mutation == "independent-acceptance":
        items[0]["independent_review"] = {"accepted": True}
    else:
        items[0]["complete_entry_review"] = False
    with pytest.raises(ReviewError):
        validate_author_reviews(candidate, SNAPSHOT, doc)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-source",
        "local-capture",
        "unknown-publisher-capture",
        "retained-known-capture",
        "later-capture",
        "nonpdf-count",
        "unused-source",
    ],
)
def test_actual_additional_capture_custody_refuses(candidate: Path, mutation: str) -> None:
    """Reject changed metadata on the genuine additional publisher captures.

    Parameters
    ----------
    candidate : pathlib.Path
        Complete actual source assessment including retained NETL and DOE captures.
    mutation : str
        Invalid source custody or source-use relationship to exercise.
    """
    doc = read(candidate / REVIEW)
    sources = cast(list[dict[str, object]], doc["additional_sources"])
    assert sources
    source = sources[0]
    if mutation == "duplicate-source":
        source["id"] = cast(list[dict[str, object]], read(candidate / PROFILE)["sources"])[0]["id"]
    elif mutation == "local-capture":
        source["captured_at"] = "2026-10-08T07:28:31+01:00"
    elif mutation == "unknown-publisher-capture":
        source["captured_at"] = None
    elif mutation == "retained-known-capture":
        source["capture_method"] = "retained-source-review"
    elif mutation == "later-capture":
        source["captured_at"] = "2030-01-01T00:00:00Z"
    elif mutation == "nonpdf-count":
        source["page_count"] = 1
    else:
        unused = dict(source)
        unused["id"] = "unused-" + str(source["id"])
        sources.append(unused)
    expected = (
        "^Author review includes an unused additional source\\.$"
        if mutation == "unused-source"
        else None
    )
    with pytest.raises(ReviewError, match=expected):
        validate_author_reviews(candidate, SNAPSHOT, doc)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-observation",
        "unknown-source",
        "pdf-bounds",
        "pdf-cardinality",
        "html-pages",
        "invalid-month",
        "invalid-year",
        "future-attained",
        "event-after-publication",
        "future-publication",
        "publication-after-capture",
    ],
)
def test_source_specific_locators_and_temporal_roles_refuse(candidate: Path, mutation: str) -> None:
    """Refuse malformed real locators and chronology without upgrading source events.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine additional observations and original whole-catalogue evidence.
    mutation : str
        Named observation or temporal contradiction applied to the actual input.
    """
    doc = read(candidate / REVIEW)
    observations = [
        item for row in records(doc) for item in cast(list[dict[str, object]], row["observations"])
    ]
    pdf = next(item for item in observations if item["pdf_pages"])
    html = next(item for item in observations if not item["pdf_pages"])
    if mutation == "duplicate-observation":
        observations[-1]["id"] = observations[0]["id"]
    elif mutation == "unknown-source":
        pdf["source_id"] = "absent-source"
    elif mutation == "pdf-bounds":
        pdf["pdf_pages"] = [100000]
        pdf["printed_pages"] = ["outside"]
    elif mutation == "pdf-cardinality":
        pdf["printed_pages"] = []
    elif mutation == "html-pages":
        html["pdf_pages"] = [1]
        html["printed_pages"] = ["1"]
    elif mutation == "invalid-month":
        pdf["event_date"] = {"value": "2024-13", "precision": "month"}
    elif mutation == "invalid-year":
        pdf["event_date"] = {"value": "0000", "precision": "year"}
    elif mutation == "future-attained":
        pdf["event_date"] = {"value": "2030-01-01", "precision": "day"}
    elif mutation == "event-after-publication":
        pdf["published_date"] = {"value": "2023", "precision": "year"}
    elif mutation == "future-publication":
        pdf["published_date"] = {"value": "2030", "precision": "year"}
    else:
        source = next(
            item
            for item in cast(list[dict[str, object]], doc["additional_sources"])
            if item["id"] == html["source_id"]
        )
        published = cast(dict[str, str | None], html["published_date"])
        published_value = published["value"]
        assert published_value is not None
        source["captured_at"] = f"{int(published_value[:4]) - 1:04d}-01-01T00:00:00Z"
    with pytest.raises(ReviewError):
        validate_author_reviews(candidate, SNAPSHOT, doc)


def test_missing_input_and_changed_baseline_are_caller_safe(candidate: Path) -> None:
    """Reject missing assessment and damaged baseline inputs through the public API.

    Parameters
    ----------
    candidate : pathlib.Path
        Owned complete source inputs, altered only by this refusal case.
    """
    (candidate / REVIEW).unlink()
    with pytest.raises(ReviewError, match="strict JSON"):
        validate_author_reviews(candidate, SNAPSHOT)
    (candidate / PROFILE).write_text("{}")
    with pytest.raises(ReviewError, match="Original evidence profile"):
        validate_author_reviews(candidate, SNAPSHOT)


@pytest.mark.parametrize("payload", ["duplicate", "nan", "overflow", "nonobject", "invalid-json"])
def test_strict_json_real_cli_refuses(candidate: Path, payload: str) -> None:
    """Reject decoder extensions and malformed full documents through the actual CLI.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine inputs with one deliberately damaged assessment file.
    payload : str
        Invalid encoding or JSON extension applied to the existing full input.
    """
    original = (candidate / REVIEW).read_text()
    if payload == "duplicate":
        raw = original.replace(
            '"schema_version":', '"schema_version":"duplicate", "schema_version":', 1
        )
    elif payload in {"nan", "overflow"}:
        raw = original.replace(
            '"original_value": null',
            '"original_value": ' + ("NaN" if payload == "nan" else "1e999"),
            1,
        )
    elif payload == "nonobject":
        raw = "[" + original + "]"
    else:
        raw = "{"
    (candidate / REVIEW).write_text(raw)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(candidate),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(candidate / REVIEW),
        ],
        cwd=candidate.parent,
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 1 and "author reviews:" in result.stderr
    assert "Traceback" not in result.stderr and str(candidate) not in result.stderr


def test_decimal_original_context_is_not_rewritten(candidate: Path) -> None:
    """Pass native decimal decoding before refusing its mismatch with actual original context.

    Parameters
    ----------
    candidate : pathlib.Path
        Real assessment whose absent original score is intentionally replaced.
    """
    raw = (
        (candidate / REVIEW)
        .read_text()
        .replace('"original_value": null', '"original_value": 0.5', 1)
    )
    (candidate / REVIEW).write_text(raw)
    with pytest.raises(ReviewError, match="original taxonomy value"):
        validate_author_reviews(candidate, SNAPSHOT)


@pytest.mark.parametrize("damage", ["schema-invalid", "schema-weakened", "schema-missing"])
def test_real_owner_copy_refuses_damaged_schema(candidate: Path, damage: str) -> None:
    """Execute unchanged owning code against actual damaged schema copies.

    Parameters
    ----------
    candidate : pathlib.Path
        Owned complete original data and assessment inputs.
    damage : str
        Owning schema fault applied after exact production-source copying.
    """
    source_paths = [
        "metadata/evidence_profiles/review_contract.py",
        "metadata/evidence_profiles/validate.py",
        "metadata/evidence_profiles/profiles.schema.json",
        "metadata/evidence_profiles/author_review.schema.json",
        "04_interactive_presentation/taxonomy-construction.js",
        "04_interactive_presentation/scripts/taxonomy_citations.cjs",
        "metadata/evidence_profiles/review_dimensions.py",
    ]
    for name in source_paths:
        path = candidate / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, path)
        assert path.read_bytes() == (ROOT / name).read_bytes()
    schema_path = candidate / source_paths[3]
    schema = read(schema_path)
    if damage == "schema-invalid":
        schema["type"] = "not-a-json-schema-type"
        schema_path.write_text(json.dumps(schema))
    elif damage == "schema-missing":
        schema_path.unlink()
    else:
        definitions = cast(dict[str, dict[str, object]], schema["$defs"])
        entry = definitions["entry"]
        fields = cast(dict[str, dict[str, object]], entry["properties"])["fields"]
        cast(list[str], fields["required"]).remove("temp")
        cast(dict[str, object], fields["properties"]).pop("temp")
        schema_path.write_text(json.dumps(schema))
        doc = read(candidate / REVIEW)
        for record in records(doc):
            cast(dict[str, object], record["fields"]).pop("temp")
        (candidate / REVIEW).write_text(json.dumps(doc))
    result = run_owner_cli(
        [
            sys.executable,
            str(candidate / source_paths[0]),
            "--root",
            str(candidate),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(candidate / REVIEW),
        ],
        candidate,
        candidate.parent,
    )
    expected = {
        "schema-invalid": "Author review schema is unavailable.",
        "schema-weakened": "Author review omits an original taxonomy field.",
        "schema-missing": "Author review input cannot be read as strict JSON.",
    }[damage]
    assert result.returncode == 1 and not result.stdout
    assert result.stderr == "author reviews: " + expected + "\n"
    assert "Traceback" not in result.stderr and str(candidate) not in result.stderr


@pytest.mark.parametrize("valid_change", [False, True])
def test_actual_profile_change_during_admission_refuses(
    candidate: Path, valid_change: bool
) -> None:
    """Refuse a real concurrent baseline rewrite after the assessment file is opened.

    Parameters
    ----------
    candidate : pathlib.Path
        Complete owned source inputs; canonical inputs are untouched.
    valid_change : bool
        Whether the rewrite remains valid original profile metadata or breaks its schema.
    """
    import time
    from threading import Event, Thread

    review_path = candidate / REVIEW
    observed = review_path.stat()
    os.utime(review_path, ns=(0, observed.st_mtime_ns))
    changed = Event()
    baseline = read(candidate / PROFILE)
    if valid_change:
        parameters = cast(list[dict[str, object]], records(baseline)[0]["parameters"])
        parameters[0]["reason"] = (
            str(parameters[0]["reason"]) + " Baseline changed during admission."
        )
        replacement = json.dumps(baseline)
    else:
        replacement = "{}"

    def rewrite() -> None:
        """Rewrite the owned baseline only after the actual assessment read begins."""
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if review_path.stat().st_atime_ns != 0:
                (candidate / PROFILE).write_text(replacement)
                changed.set()
                return
            time.sleep(0.001)

    worker = Thread(target=rewrite)
    worker.start()
    try:
        with pytest.raises(ReviewError, match="changed during assessment"):
            validate_author_reviews(candidate, SNAPSHOT)
    finally:
        worker.join(timeout=35)
    assert changed.is_set() and not worker.is_alive()
