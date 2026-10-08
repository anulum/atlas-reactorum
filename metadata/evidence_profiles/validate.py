#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/evidence_profiles/validate.py

"""Read complete evidence profiles bound to an explicit catalogue snapshot.

This is a catalogue metadata contract. Source inspection, provisional entity
mapping, independent review and redistribution rights remain separate. The
original citation reader owns its source and page-locator validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess  # nosec B404 # Import creates no process; the native call is scoped below.
import sys
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker

KINDS = {
    "architecture": "architecture",
    "subtype": "subtype",
    "development class": "development-class",
    "research-reactor geometry": "geometry",
    "liquid-fuel research architecture": "architecture",
    "research configuration": "configuration",
    "operating mode": "operating-mode",
    "ignition scheme": "ignition-scheme",
    "device": "device",
    "configuration": "configuration",
    "process class": "process-class",
    "coupled reactor architecture": "architecture",
    "operating configuration": "configuration",
    "application architecture": "architecture",
    "system integration": "system-integration",
}
INPUTS = {
    "taxonomy_sha256": "04_interactive_presentation/data/taxonomy-expanded.js",
    "citations_sha256": "metadata/taxonomy_audit/claim_citations.json",
    "audit_sha256": "metadata/taxonomy_audit/audit.tsv",
}
LEGACY_PROGRAM = """
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.argv[1];
const window = {};
const construction = require(path.resolve(path.dirname(process.argv[2]),
  '../taxonomy-construction.js'));
vm.runInNewContext(fs.readFileSync(path.join(root,
  '04_interactive_presentation/data/taxonomy-expanded.js'), 'utf8'),
  {window, AtlasTaxonomyConstruction: construction});
const rows = JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY));
const {readCitations} = require(process.argv[2]);
readCitations(root, rows);
process.stdout.write(JSON.stringify(rows));
"""


class ProfileError(ValueError):
    """Refuse an incomplete, stale or unsupported evidence profile."""


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProfileError("Duplicate JSON member.")
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ProfileError("Nonfinite JSON number.")


def _float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ProfileError("Nonfinite JSON number.")
    return result


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProfileError("Expected a JSON object.")
    # JSON decoding supplies string keys; schema/legacy validation owns members.
    return cast(dict[str, object], value)


def _array(value: object) -> list[object]:
    # Both callers have already passed the complete schema or legacy reader.
    return cast(list[object], value)


def _text(value: object) -> str:
    return cast(str, value)


def _load(path: Path) -> dict[str, object]:
    try:
        value: object = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
            parse_float=_float,
        )
        return _object(value)
    except (OSError, UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ProfileError("Profile input cannot be read as strict JSON.") from error


def _input_hashes(root: Path) -> dict[str, str]:
    try:
        return {
            field: hashlib.sha256((root / relative).read_bytes()).hexdigest()
            for field, relative in INPUTS.items()
        }
    except OSError as error:
        raise ProfileError("Frozen input cannot be read.") from error


def _legacy(root: Path) -> tuple[dict[str, object], list[object], dict[str, dict[str, str]]]:
    legacy = _load(root / INPUTS["citations_sha256"])
    reader = Path(__file__).resolve().parents[2] / (
        "04_interactive_presentation/scripts/taxonomy_citations.cjs"
    )
    executable = shutil.which("node")
    if executable is None:
        raise ProfileError("Native Node reader is unavailable.")
    try:
        result = subprocess.run(  # nosec B603 # Trusted local Node and fixed legacy-reader program; finite deadline.
            [executable, "-e", LEGACY_PROGRAM, str(root), str(reader)],
            capture_output=True,
            timeout=30,
            check=False,
            encoding="utf-8",
        )
        if result.returncode:
            raise ProfileError("Legacy citation validation failed.")
        rows = _array(json.loads(result.stdout))
        with (root / INPUTS["audit_sha256"]).open(encoding="utf-8", newline="") as handle:
            audits = list(csv.DictReader(handle, delimiter="\t"))
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as error:
        raise ProfileError("Legacy inputs cannot be validated.") from error
    identities = [None, *[_object(row)["id"] for row in rows]]
    if any(_object(row).get("parent_id") not in identities for row in rows):
        raise ProfileError("Catalogue parent refers to an unknown entry.")
    if any(
        set(row)
        != {
            "id",
            "name",
            "classification_ok",
            "source_directness",
            "source_access",
            "issue",
            "recommended_action",
            "verified_source_url",
            "audit_date",
        }
        or any(not isinstance(value, str) for value in row.values())
        for row in audits
    ):
        raise ProfileError("Historical audit structure is invalid.")
    by_id = {row["id"]: row for row in audits}
    if len(by_id) != len(audits) or set(by_id) != {_object(row)["id"] for row in rows}:
        raise ProfileError("Historical audit identities are incomplete or duplicated.")
    return legacy, rows, by_id


def validate_profiles(
    root: Path, snapshot_sha256: str, document: dict[str, object] | None = None
) -> dict[str, object]:
    """Validate the entire profile document before returning any record.

    Parameters
    ----------
    root : pathlib.Path
        Complete repository or candidate containing the frozen catalogue inputs.
    snapshot_sha256 : str
        Explicit expected SHA-256 of the taxonomy source, never an implicit latest.
    document : dict of str to object or None
        Whole document to validate in memory; None reads the authored profile input.

    Returns
    -------
    dict of str to object
        Complete versioned document with all original source metadata and claims.

    Raises
    ------
    ProfileError
        The schema, snapshot, full record set or any source binding is invalid.
    """
    if document is None:
        document = _load(root / "metadata/evidence_profiles/profiles.json")
    schema = _load(Path(__file__).with_name("profiles.schema.json"))
    if next(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document), None
    ):
        raise ProfileError("Evidence profile schema validation failed.")
    inputs = _object(document["inputs"])
    if inputs["taxonomy_sha256"] != snapshot_sha256:
        raise ProfileError("Requested taxonomy snapshot does not match.")
    if inputs != _input_hashes(root):
        raise ProfileError("Evidence profile input hash is stale.")
    legacy, rows, audits = _legacy(root)
    if document["sources"] != legacy["sources"]:
        raise ProfileError("Source metadata differs from the original catalogue.")
    records = _array(document["records"])
    originals = _array(legacy["records"])
    if document["record_count"] != len(rows) or len(records) != len(rows):
        raise ProfileError("Evidence profiles must cover the complete catalogue.")
    for index, value in enumerate(records):
        profile = _object(value)
        original = _object(originals[index])
        row = _object(rows[index])
        entry_id = _text(original["id"])
        kind = _text(_object(original["values"])["kind"])
        if kind not in KINDS:
            raise ProfileError("Catalogue kind has no declared entity mapping.")
        if profile["entry_id"] != entry_id or profile["bound_values"] != original["values"]:
            raise ProfileError("Entry order, identity or bound values differ.")
        if profile["taxonomy_record"] != row:
            raise ProfileError("Original taxonomy context differs.")
        if profile["legacy_kind"] != kind or _object(profile["entity_kind"]) != {
            "category": KINDS[kind],
            "basis": "legacy-kind-mapping",
            "decision": "provisional",
        }:
            raise ProfileError("Entity mapping is not the declared provisional mapping.")
        citations = [_object(item) for item in _array(original["citations"])]
        expected_claims = [
            {
                "claim_id": citation["id"],
                "topic": citation["topic"],
                "original_statement": citation["statement"],
                "citation": citation,
            }
            for citation in citations
        ]
        if profile["claims"] != expected_claims:
            raise ProfileError("Claim support differs from the original source inspection.")
        audit = audits[entry_id]
        expected_review = {
            "complete_entry_review": False,
            "source_inspection": {
                "basis": "author-source-inspection",
                "author": None,
                "claim_ids": [citation["id"] for citation in citations],
                "source_snapshot_sha256": inputs["citations_sha256"],
            },
            "classification": {
                "state": "open",
                "basis": "legacy-kind-mapping",
                "questions": [audit["issue"], audit["recommended_action"]],
            },
            "independent_review": None,
            "historical_audit": audit,
        }
        if profile["review_disposition"] != expected_review:
            raise ProfileError("Review scope or historical decisions were changed.")
        parameters = [_object(item) for item in _array(profile["parameters"])]
        if len({_text(item["id"]) for item in parameters}) != len(parameters):
            raise ProfileError("Duplicate parameter identity.")
        claims = {_text(citation["id"]) for citation in citations}
        for parameter in parameters:
            if parameter["state"] == "known":
                try:
                    finite = math.isfinite(cast(int | float, parameter["value"]))
                except OverflowError as error:
                    raise ProfileError(
                        "Normalized parameter is not a finite representable value."
                    ) from error
                if not finite:
                    raise ProfileError("Normalized parameter is not a finite representable value.")
                if not set(map(_text, _array(parameter["claim_ids"]))).issubset(claims):
                    raise ProfileError("Normalized parameter cites an unknown claim.")
            elif parameter["id"] == "temperature" and parameter["original_text"] != row["temp"]:
                raise ProfileError("Original temperature text was changed.")
    if inputs != _input_hashes(root):
        raise ProfileError("Frozen inputs changed during validation.")
    return document


def migrate_profiles(root: Path, snapshot_sha256: str) -> dict[str, object]:
    """Project every original catalogue record into the versioned profile contract.

    Parameters
    ----------
    root : pathlib.Path
        Complete candidate with the original citations and historical audit.
    snapshot_sha256 : str
        Explicit selected taxonomy source hash.

    Returns
    -------
    dict of str to object
        Validated whole-catalogue migration; this function writes no input or product.

    Raises
    ------
    ProfileError
        Frozen source inputs or the resulting complete profile cannot be validated.
    """
    legacy, rows, audits = _legacy(root)
    inputs = _input_hashes(root)
    profiles: list[object] = []
    for value, row_value in zip(_array(legacy["records"]), rows, strict=True):
        original = _object(value)
        row = _object(row_value)
        entry_id = _text(original["id"])
        kind = _text(_object(original["values"])["kind"])
        if kind not in KINDS:
            raise ProfileError("Catalogue kind has no declared entity mapping.")
        citations = [_object(item) for item in _array(original["citations"])]
        audit = audits[entry_id]
        profiles.append(
            {
                "entry_id": entry_id,
                "legacy_kind": kind,
                "entity_kind": {
                    "category": KINDS[kind],
                    "basis": "legacy-kind-mapping",
                    "decision": "provisional",
                },
                "bound_values": original["values"],
                "taxonomy_record": row,
                "claims": [
                    {
                        "claim_id": item["id"],
                        "topic": item["topic"],
                        "original_statement": item["statement"],
                        "citation": item,
                    }
                    for item in citations
                ],
                "parameters": [
                    {
                        "id": "temperature",
                        "state": "not_reviewed",
                        "reason": "The catalogue text has not been normalized with source-bound units, conditions and a system boundary.",
                        "original_text": row["temp"],
                    }
                ],
                "review_disposition": {
                    "complete_entry_review": False,
                    "source_inspection": {
                        "basis": "author-source-inspection",
                        "author": None,
                        "claim_ids": [item["id"] for item in citations],
                        "source_snapshot_sha256": inputs["citations_sha256"],
                    },
                    "classification": {
                        "state": "open",
                        "basis": "legacy-kind-mapping",
                        "questions": [audit["issue"], audit["recommended_action"]],
                    },
                    "independent_review": None,
                    "historical_audit": audit,
                },
            }
        )
    return validate_profiles(
        root,
        snapshot_sha256,
        {
            "schema_version": "1.0.0",
            "record_count": len(profiles),
            "inputs": inputs,
            "sources": legacy["sources"],
            "records": profiles,
        },
    )


def read_profile(root: Path, snapshot_sha256: str, entry_id: str) -> dict[str, object]:
    """Read one entry only after validating the complete explicit snapshot.

    Parameters
    ----------
    root : pathlib.Path
        Complete candidate root.
    snapshot_sha256 : str
        SHA-256 selected by the caller.
    entry_id : str
        Stable catalogue identity.

    Returns
    -------
    dict of str to object
        The exact authored profile, without fabricated review or capture dates.

    Raises
    ------
    ProfileError
        Any record is invalid or the selected identity does not exist.
    """
    for value in _array(validate_profiles(root, snapshot_sha256)["records"]):
        profile = _object(value)
        if profile["entry_id"] == entry_id:
            return profile
    raise ProfileError("Requested entry does not exist in this snapshot.")


def main(argv: list[str] | None = None) -> int:
    """Validate a whole snapshot or print one explicitly selected profile.

    Parameters
    ----------
    argv : list of str or None
        CLI arguments; None uses the native process arguments.

    Returns
    -------
    int
        Zero for a validated document, one for a safe refusal.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--entry")
    parser.add_argument(
        "--migrate", action="store_true", help="Print the complete migration without writing files"
    )
    args = parser.parse_args(argv)
    try:
        if args.migrate:
            if args.entry is not None:
                raise ProfileError("Migration cannot select only one entry.")
            document = migrate_profiles(args.root, args.snapshot)
        elif args.entry is None:
            document = validate_profiles(args.root, args.snapshot)
        else:
            document = read_profile(args.root, args.snapshot, args.entry)
    except ProfileError as error:
        # Only fixed validator messages are exposed, never source bodies or paths.
        print("evidence profiles: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
