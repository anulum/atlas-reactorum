#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round2/validate.py
"""Validate the Canada/Australia industrial discovery expansion."""

from __future__ import annotations

import argparse
import csv
import math
import subprocess  # nosec B404 # Import creates no process; calls have scoped reviews.
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "industrial_facilities_round2.tsv"
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
REGISTRY = ROOT / "source_registry.tsv"
FIELDS = [
    "stable_id",
    "facility_name",
    "country",
    "lat",
    "lon",
    "precision",
    "sector",
    "process_or_activity",
    "reactor_type_if_explicit",
    "status",
    "operator",
    "capacity",
    "pollutant_or_product_context",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]
SNAPSHOT_FIELDS = [
    "source",
    "source_record_id",
    "latest_report_year",
    "facility_name",
    "operator",
    "country",
    "lat",
    "lon",
    "sector_code",
    "sector_label",
    "process_code",
    "process_label",
    "main_activities",
    "datum",
    "source_row_url",
]


MANIFEST_FIELDS = ["source", "url", "retrieved", "bytes", "sha256", "selected_rows"]
REGISTRY_FIELDS = [
    "source_id",
    "title",
    "url",
    "publisher",
    "role",
    "license",
    "retrieved",
    "notes",
]
EXPECTED_SOURCE = {"canada-npri": 908, "australia-npi": 868}
EXPECTED_COUNTRY = {"Canada": 908, "Australia": 868}
REQUIRED = (
    "facility_name",
    "country",
    "lat",
    "lon",
    "precision",
    "sector",
    "process_or_activity",
    "status",
    "operator",
    "source_url",
    "source_role",
    "license",
    "verification_notes",
)


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a nonempty exact-schema TSV, rejecting malformed rows and quoting."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header {reader.fieldnames}")
        rows: list[dict[str, str]] = []
        for raw in reader:
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f"{path.name}: row has the wrong width")
            rows.append({field: raw[field] for field in fields})
    if not rows:
        raise ValueError(f"{path.name}: contains no records")
    return rows


def valid_https(value: str) -> bool:
    """Check that a cited source is a valid anonymous HTTPS URL."""
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.port != 0
            and not any(c.isspace() for c in value)
        )
    except ValueError:
        return False


def validate_records(
    rows: list[dict[str, str]],
    snapshot: list[dict[str, str]],
    manifest: list[dict[str, str]],
    registry: list[dict[str, str]],
) -> list[str]:
    """Check the historical counts, provenance and non-inference invariants."""
    for records, fields in (
        (rows, FIELDS),
        (snapshot, SNAPSHOT_FIELDS),
        (manifest, MANIFEST_FIELDS),
        (registry, REGISTRY_FIELDS),
    ):
        if any(
            set(r) != set(fields) or any(not isinstance(v, str) for v in r.values())
            for r in records
        ):
            return ["record differs from its required string schema"]
    errors: list[str] = []
    if len(rows) != 1776 or len(snapshot) != 1776:
        errors.append(f"expected 1776 data/snapshot rows; got {len(rows)}/{len(snapshot)}")
    if Counter(row["country"] for row in rows) != Counter(EXPECTED_COUNTRY):
        errors.append("unexpected country counts")
    if Counter(row["source"] for row in snapshot) != Counter(EXPECTED_SOURCE):
        errors.append("unexpected snapshot source counts")
    for stable_id, count in Counter(row["stable_id"] for row in rows).items():
        if not stable_id or count != 1:
            errors.append(f"duplicate/empty stable_id {stable_id!r}: {count}")
    for row in rows:
        key = row["stable_id"]
        for field in REQUIRED:
            if not row[field].strip():
                errors.append(f"{key}: missing {field}")
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                errors.append(f"{key}: coordinate out of range")
        except ValueError:
            errors.append(f"{key}: non-numeric coordinate")
        if row["reactor_type_if_explicit"]:
            errors.append(f"{key}: reactor type must remain empty for these sources")
        if row["capacity"]:
            errors.append(f"{key}: capacity must remain empty for this field-minimised layer")
        if row["retrieved"] != "2026-09-27":
            errors.append(f"{key}: wrong retrieval date")
        if not valid_https(row["source_url"]):
            errors.append(f"{key}: invalid HTTPS source URL")
        if "operating status not asserted" not in row["status"]:
            errors.append(f"{key}: status overclaims operation")
    if len(manifest) != 2 or {row["source"] for row in manifest} != set(EXPECTED_SOURCE):
        errors.append("source manifest must contain exactly the two official sources")
    for row in manifest:
        source = row["source"]
        if len(row["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["sha256"]):
            errors.append(f"manifest has invalid SHA-256 for {source}")
        if row["retrieved"] != "2026-09-27":
            errors.append(f"manifest wrong retrieval date for {source}")
        if not valid_https(row["url"]):
            errors.append(f"manifest invalid HTTPS URL for {source}")
        try:
            if int(row["selected_rows"]) != EXPECTED_SOURCE.get(source) or int(row["bytes"]) <= 0:
                raise ValueError("wrong manifest counts")
        except ValueError:
            errors.append(f"manifest selected row count or byte count mismatch for {source}")
    if len(registry) < 5:
        errors.append("source registry is unexpectedly short")
    ids = [row["source_id"] for row in registry]
    if any(not source for source in ids) or len(set(ids)) != len(ids):
        errors.append("source registry IDs must be nonempty and unique")
    for row in registry:
        if row["retrieved"] != "2026-09-27" or not valid_https(row["url"]):
            errors.append(f"source registry invalid record: {row['source_id']}")
        if any(not row[field].strip() for field in ("title", "publisher", "role", "license")):
            errors.append(f"source registry missing provenance: {row['source_id']}")
    return errors


def verify_rebuild(data: Path, snapshot: Path, *, timeout: float = 30) -> bool:
    """Run the actual offline producer into a temporary output and compare bytes.

    Neither the requested data nor the historical snapshots are rewritten.
    A failed or timed-out native producer cannot prove reproducibility.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("rebuild timeout must be positive and finite")
    with tempfile.TemporaryDirectory(prefix="atlas-industrial-validation-") as directory:
        output = Path(directory) / "rebuilt.tsv"
        try:
            # Fixed sibling script; data paths are separate argv; no shell; finite deadline.
            completed = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    str(ROOT / "build_dataset.py"),
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False
        if completed.returncode:
            return False
        return data.read_bytes() == output.read_bytes()


def main(argv: list[str] | None = None) -> int:
    """Validate explicit read-only inputs and prove their native offline rebuild."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        errors = validate_records(
            read(args.data, FIELDS),
            read(args.snapshot, SNAPSHOT_FIELDS),
            read(args.manifest, MANIFEST_FIELDS),
            read(args.registry, REGISTRY_FIELDS),
        )
        if not errors and not verify_rebuild(args.data, args.snapshot, timeout=args.timeout):
            errors.append("offline rebuild from compact snapshot is not deterministic")
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print("FAIL")
        for error in errors:
            print("-", error)
        return 1
    print(
        "PASS: 1,776 licensed facility records; deterministic offline rebuild; no inferred reactor types or coordinates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
