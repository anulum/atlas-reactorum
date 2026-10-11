# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete original/current product admission.

"""Validate genuinely emitted reviewed products through Python API/CLI and Node."""

from __future__ import annotations

import errno
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from threading import Event, Thread
from typing import cast

import pytest

from metadata.evidence_profiles.review_contract import ReviewError
from metadata.evidence_profiles.reviewed_profiles import validate_reviewed_profiles
from metadata.evidence_profiles.validate import INPUTS

from .test_author_review_contract import PROFILE, REVIEW, ROOT, SNAPSHOT, read, run_owner_cli
from .test_author_review_contract import candidate as candidate

PRODUCT = Path("04_interactive_presentation/data/taxonomy-reviewed-profiles.json")
SCRIPT = ROOT / "metadata/evidence_profiles/reviewed_profiles.py"


@pytest.fixture(scope="module")
def genuine_products(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Produce genuine complete source-bound products before isolated consumer cases.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Samsung-owned allocation for original/author inputs and actual products.

    Returns
    -------
    pathlib.Path
        Real Node-produced product tree, unchanged by individual refusal cases.
    """
    source = Path(os.environ.get("ATLAS_AUTHOR_REVIEW_INPUT", str(ROOT / REVIEW)))
    candidate = tmp_path_factory.mktemp("genuine-reviewed-products")
    for relative in [*INPUTS.values(), str(PROFILE)]:
        target = candidate / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    shutil.copy2(source, candidate / REVIEW)
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [
            node,
            str(ROOT / "04_interactive_presentation/scripts/export_taxonomy.cjs"),
            "--root",
            str(candidate),
            "--reviews",
            str(candidate / REVIEW),
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 0, result.stderr
    return candidate


@pytest.fixture
def emitted(candidate: Path, genuine_products: Path) -> Path:
    """Copy exact genuine product bytes into each isolated native consumer case.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine complete original and author input bytes for this case.
    genuine_products : pathlib.Path
        Independently retained actual Node-generated complete products.

    Returns
    -------
    pathlib.Path
        Owned source and unmodified generated JSON/JS before deliberate faults.
    """
    for name in ["taxonomy-reviewed-profiles.json", "taxonomy-reviewed-profiles.js"]:
        target = candidate / PRODUCT.parent / name
        shutil.copy2(genuine_products / PRODUCT.parent / name, target)
    return candidate


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "shape",
        "version",
        "count",
        "boolean-count",
        "fractional-count",
        "rights",
        "license",
        "hash",
        "original",
        "author",
        "current",
        "last-current",
        "missing-source",
    ],
)
def test_actual_whole_reviewed_product_admission(emitted: Path, fault: str) -> None:
    """Retain every original profile or reject actual complete-product corruption.

    Parameters
    ----------
    emitted : pathlib.Path
        Real original/current product built from genuine all135 source inputs.
    fault : str
        Actual shape, source or current-context fault introduced after production.
    """
    doc = read(emitted / PRODUCT)
    original = (emitted / PROFILE).read_bytes()
    if fault == "shape":
        doc["extra"] = True
    elif fault == "version":
        doc["schema_version"] = "unknown"
    elif fault == "count":
        doc["record_count"] = 134
    elif fault == "boolean-count":
        doc["record_count"] = True
    elif fault == "fractional-count":
        doc["record_count"] = 135.0
    elif fault == "rights":
        doc["source_rights"] = "unrestricted"
    elif fault == "license":
        doc["metadata_license"] = "unknown"
    elif fault == "hash":
        cast(dict[str, object], doc["inputs"])["author_reviews_sha256"] = "0" * 64
    elif fault == "original":
        source = cast(dict[str, object], doc["original_profiles"])
        cast(list[dict[str, object]], source["records"])[0]["entry_id"] = "changed"
    elif fault == "author":
        cast(dict[str, object], doc["author_reviews"])["author"] = "changed"
    elif fault in {"current", "last-current"}:
        cast(list[dict[str, object]], doc["records"])[0 if fault == "current" else -1]["name"] = (
            "unassessed caption"
        )
    elif fault == "missing-source":
        (emitted / REVIEW).unlink()
    if fault == "none":
        assert validate_reviewed_profiles(emitted, SNAPSHOT, emitted / REVIEW, doc) == doc
        assert validate_reviewed_profiles(emitted, SNAPSHOT, emitted / REVIEW) == doc
        assert len(cast(list[object], doc["records"])) == 135
        assert cast(dict[str, object], doc["original_profiles"]) == read(emitted / PROFILE)
    else:
        with pytest.raises(ReviewError):
            validate_reviewed_profiles(emitted, SNAPSHOT, emitted / REVIEW, doc)
    assert (emitted / PROFILE).read_bytes() == original


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("explicit", [False, True])
def test_actual_reviewed_profile_cli(emitted: Path, optimized: bool, explicit: bool) -> None:
    """Admit the full genuine product in both process modes and input selections.

    Parameters
    ----------
    emitted : pathlib.Path
        Real complete source-bound product and its actual inputs.
    optimized : bool
        Whether the process runs under Python optimization.
    explicit : bool
        Whether the product input path is explicit or owning default.
    """
    before = (emitted / PRODUCT).read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimized else []),
            str(SCRIPT),
            "--root",
            str(emitted),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(emitted / REVIEW),
            *(["--input", str(emitted / PRODUCT)] if explicit else []),
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == read(emitted / PRODUCT)
    assert (emitted / PRODUCT).read_bytes() == before


@pytest.mark.parametrize("source", ["profile", "review", "restored-review"])
def test_real_composer_rejects_concurrent_source_changes(candidate: Path, source: str) -> None:
    """Use actual file reads, atomic replacements and the public product composer.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine complete original and author input tree.
    source : str
        Source byte drift or temporarily changed author content restored before return.
    """
    watched = candidate / (PROFILE if source == "profile" else REVIEW)
    before = watched.read_bytes()
    changed = json.loads(before)
    if source == "profile":
        changed["records"][0]["parameters"][0]["reason"] += " Concurrent source change."
    else:
        changed["records"][0]["fields"]["id"]["assessment"] += " Concurrent author context."
    original_path = candidate / "original-validated.json"
    original_path.write_bytes((ROOT / PROFILE).read_bytes())
    old_stat = watched.stat()
    os.utime(watched, ns=(0, old_stat.st_mtime_ns))
    completed = Event()

    def replace() -> None:
        """Replace only after the composer's first real source read; optionally restore."""
        deadline = time.monotonic() + 45
        while watched.stat().st_atime_ns == 0 and time.monotonic() < deadline:
            time.sleep(0.001)
        replacement = candidate / "source-replacement.json"
        replacement.write_text(json.dumps(changed))
        if source == "restored-review":
            info = replacement.stat()
            os.utime(replacement, ns=(0, info.st_mtime_ns))
        replacement.replace(watched)
        if source == "restored-review":
            while watched.stat().st_atime_ns == 0 and time.monotonic() < deadline:
                time.sleep(0.001)
            restore = candidate / "source-restore.json"
            restore.write_bytes(before)
            restore.replace(watched)
        completed.set()

    node = shutil.which("node")
    assert node is not None
    worker = Thread(target=replace)
    worker.start()
    try:
        program = "const fs=require('node:fs');const api=require(process.argv[1]);const original=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));try{api.reviewedProducts(process.argv[3],original.inputs.taxonomy_sha256,original,process.argv[4]);process.stdout.write('accepted');}catch(error){process.stdout.write(error.message);}"
        result = subprocess.run(
            [
                node,
                "-e",
                program,
                str(ROOT / "04_interactive_presentation/scripts/taxonomy_reviewed_products.cjs"),
                str(original_path),
                str(candidate),
                str(candidate / REVIEW),
            ],
            capture_output=True,
            text=True,
            timeout=65,
        )
    finally:
        worker.join(timeout=50)
    assert completed.is_set() and not worker.is_alive()
    assert result.returncode == 0, result.stderr
    assert result.stdout == "Reviewed evidence: source changed during composition"
    if source == "restored-review":
        assert watched.read_bytes() == before


@pytest.mark.parametrize("change", ["review", "profile", "missing-review"])
def test_reviewed_admission_rejects_actual_late_source_drift(emitted: Path, change: str) -> None:
    """Replace an owned source after its actual author decode but before final custody checks.

    Parameters
    ----------
    emitted : pathlib.Path
        Genuine complete product and its original source files.
    change : str
        Author/profile byte drift or late disappearance of the author input.
    """
    review = emitted / REVIEW
    before = review.read_bytes()
    review.unlink()
    os.mkfifo(review)
    completed = Event()
    prepared_review = emitted / "late-review.json"
    prepared_review.write_bytes(before + (b"\n" if change == "review" else b""))
    prepared_profile = emitted / "late-profile.json"
    if change == "profile":
        original = read(emitted / PROFILE)
        parameters = cast(
            list[dict[str, object]],
            cast(list[dict[str, object]], original["records"])[0]["parameters"],
        )
        parameters[0]["reason"] = str(parameters[0]["reason"]) + " Late original context."
        prepared_profile.write_text(json.dumps(original))

    def replace() -> None:
        """Supply exact captured and decoded inputs through real owned file descriptors."""
        for packet in range(2):
            with review.open("wb") as output:
                output.write(before)
                if packet == 1:
                    if change == "profile":
                        prepared_profile.replace(emitted / PROFILE)
                    if change == "missing-review":
                        review.unlink()
                    else:
                        prepared_review.replace(review)
            if packet == 0:
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    try:
                        descriptor = os.open(review, os.O_WRONLY | os.O_NONBLOCK)
                    except OSError as error:
                        if error.errno != errno.ENXIO:
                            raise
                        break
                    else:
                        os.close(descriptor)
                    time.sleep(0.001)

        completed.set()

    worker = Thread(target=replace)
    worker.start()
    try:
        with pytest.raises(ReviewError, match="source changed during admission"):
            validate_reviewed_profiles(emitted, SNAPSHOT, review)
    finally:
        worker.join(timeout=50)
    assert completed.is_set() and not worker.is_alive()


def test_real_reviewed_cli_refuses_changed_final_record_without_traceback(emitted: Path) -> None:
    """Refuse a damaged actual complete product without exposing source paths or partial output.

    Parameters
    ----------
    emitted : pathlib.Path
        Actual complete reviewed product with only its last row intentionally damaged.
    """
    doc = read(emitted / PRODUCT)
    cast(list[dict[str, object]], doc["records"])[-1]["name"] = "unassessed last caption"
    (emitted / PRODUCT).write_text(json.dumps(doc))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(emitted),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(emitted / REVIEW),
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 1 and not result.stdout
    assert "reviewed profiles:" in result.stderr and "Traceback" not in result.stderr
    assert str(emitted) not in result.stderr


@pytest.mark.parametrize("valid_change", [False, True])
def test_final_original_validation_sees_real_changed_source(
    emitted: Path, valid_change: bool
) -> None:
    """Supply real original reads before presenting a changed final original to the public API.

    Parameters
    ----------
    emitted : pathlib.Path
        Genuine emitted whole product with actual original/profile inputs.
    valid_change : bool
        Whether the final original retains valid metadata or breaks its owning schema.
    """
    profile = emitted / PROFILE
    before = profile.read_bytes()
    changed = json.loads(before)
    changed["records"][0]["parameters"][0]["reason"] += " Final original differs."
    last = json.dumps(changed).encode() if valid_change else b"{}"
    review = emitted / REVIEW
    review_bytes = review.read_bytes()
    review.unlink()
    os.mkfifo(review)
    prepared = emitted / "final-original.json"
    prepared.write_bytes(last)
    restore = emitted / "regular-review.json"
    restore.write_bytes(review_bytes)
    completed = Event()

    def supply() -> None:
        """Fence final original validation behind the actual final review-byte read."""
        for index in range(3):
            with review.open("wb") as output:
                output.write(review_bytes)
                if index == 2:
                    prepared.replace(profile)
                    restore.replace(review)
            if index < 2:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    try:
                        descriptor = os.open(review, os.O_WRONLY | os.O_NONBLOCK)
                    except OSError as error:
                        if error.errno != errno.ENXIO:
                            raise
                        break
                    else:
                        os.close(descriptor)
                    time.sleep(0.001)
        completed.set()

    worker = Thread(target=supply)
    worker.start()
    try:
        with pytest.raises(ReviewError, match="changed during admission"):
            validate_reviewed_profiles(emitted, SNAPSHOT, emitted / REVIEW)
    finally:
        worker.join(timeout=90)
    assert completed.is_set() and not worker.is_alive()
    assert review.read_bytes() == review_bytes


@pytest.mark.parametrize("fault", ["missing", "malformed", "invalid", "reference"])
def test_real_owning_reviewed_schema_refuses_damage(emitted: Path, fault: str) -> None:
    """Refuse damage to the actual owning schema through an isolated native CLI.

    Parameters
    ----------
    emitted : pathlib.Path
        Actual complete source and generated products, retained unchanged.
    fault : str
        Missing, malformed, invalid or unresolved owning schema in an owned source copy.
    """
    owner = emitted / "owner"
    source_paths = [
        "metadata/evidence_profiles/reviewed_profiles.py",
        "metadata/evidence_profiles/reviewed_profiles.schema.json",
        "metadata/evidence_profiles/review_contract.py",
        "metadata/evidence_profiles/review_dimensions.py",
        "metadata/evidence_profiles/validate.py",
        "metadata/evidence_profiles/profiles.schema.json",
        "metadata/evidence_profiles/author_review.schema.json",
        "04_interactive_presentation/taxonomy-construction.js",
        "04_interactive_presentation/scripts/taxonomy_citations.cjs",
    ]
    for name in source_paths:
        target = owner / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        assert target.read_bytes() == (ROOT / name).read_bytes()
    schema = owner / "metadata/evidence_profiles/reviewed_profiles.schema.json"
    if fault == "missing":
        schema.unlink()
    elif fault == "malformed":
        schema.write_text("{")
    else:
        document = read(schema)
        if fault == "invalid":
            document["type"] = "no-such-type"
        else:
            cast(dict[str, object], document["properties"])["original_profiles"] = {
                "$ref": "urn:atlas-reactorum:absent"
            }
        schema.write_text(json.dumps(document))
    result = run_owner_cli(
        [
            sys.executable,
            str(owner / "metadata/evidence_profiles/reviewed_profiles.py"),
            "--root",
            str(emitted),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(emitted / REVIEW),
        ],
        owner,
        emitted.parent,
    )
    assert result.returncode == 1 and not result.stdout
    assert result.stderr == "reviewed profiles: Reviewed profile schema cannot be validated.\n"
    assert "Traceback" not in result.stderr and str(owner) not in result.stderr
