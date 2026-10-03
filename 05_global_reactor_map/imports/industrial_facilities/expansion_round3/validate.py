#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round3/validate.py
"""Validate the UK PRTR industrial-facility discovery expansion."""

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
DATA = ROOT / "industrial_facilities_round3.tsv"
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
REGISTRY = ROOT / "source_registry.tsv"
EXPECTED_ROWS = 722
NACE_PREFIXES = ("10", "11", "17", "19", "20", "21", "22")

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
    "reporting_year",
    "facility_name",
    "operator",
    "country",
    "lat",
    "lon",
    "nace_code",
    "nace_label",
    "annex_i_activity_code",
]


MANIFEST_FIELDS = [
    "source",
    "url",
    "retrieved",
    "reporting_year",
    "bytes",
    "sha256",
    "raw_rows",
    "selected_rows",
]
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
OTHER_LAYERS = (
    ROOT.parent / "industrial_facilities.tsv",
    ROOT.parent / "expansion_round2/industrial_facilities_round2.tsv",
)
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


def read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
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


def validate_records(
    rows: list[dict[str, str]],
    snapshot: list[dict[str, str]],
    manifest: list[dict[str, str]],
    registry: list[dict[str, str]],
) -> list[str]:
    """Check the complete accepted UK data, source identity and provenance."""
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
    if len(rows) != EXPECTED_ROWS or len(snapshot) != EXPECTED_ROWS:
        errors.append(
            f"expected {EXPECTED_ROWS} data/snapshot rows; got {len(rows)}/{len(snapshot)}"
        )
    ids = Counter(row["stable_id"] for row in rows)
    source_ids = Counter(row["source_record_id"] for row in snapshot)
    for stable_id, count in ids.items():
        if not stable_id or count != 1:
            errors.append(f"duplicate/empty stable_id {stable_id!r}: {count}")
    for source_id, count in source_ids.items():
        if not source_id or count != 1:
            errors.append(f"duplicate/empty source_record_id {source_id!r}: {count}")
    expected_ids = {f"uk-prtr:{row['source_record_id']}" for row in snapshot}
    if set(ids) != expected_ids:
        errors.append("output stable IDs do not match the compact source snapshot")
    for src in snapshot:
        if src["source"] != "uk-prtr" or src["reporting_year"] != "2024":
            errors.append(f"{src['source_record_id']}: unexpected source/year")
        if not src["nace_code"].startswith(NACE_PREFIXES):
            errors.append(f"{src['source_record_id']}: NACE code is outside documented filter")
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
        if row["country"] != "United Kingdom":
            errors.append(f"{key}: unexpected country")
        if row["reactor_type_if_explicit"] or row["capacity"]:
            errors.append(f"{key}: reactor type and capacity must remain empty")
        if row["retrieved"] != "2026-09-28":
            errors.append(f"{key}: wrong retrieval date")
        if "operating status not asserted" not in row["status"]:
            errors.append(f"{key}: status overclaims operation")
        if not valid_https(row["source_url"]):
            errors.append(f"{key}: source URL must be valid anonymous HTTPS")
    if len(manifest) != 1 or manifest[0]["source"] != "uk-prtr":
        errors.append("source manifest must contain exactly the UK PRTR raw source")
    else:
        item = manifest[0]
        digest = item["sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append("manifest has invalid SHA-256")
        if item["retrieved"] != "2026-09-28" or item["reporting_year"] != "2024":
            errors.append("manifest has unexpected retrieval/report year")
        try:
            if (
                int(item["selected_rows"]) != EXPECTED_ROWS
                or int(item["bytes"]) <= 0
                or int(item["raw_rows"]) < EXPECTED_ROWS
            ):
                raise ValueError("invalid manifest counts")
        except ValueError:
            errors.append("manifest selected-row, raw-row or byte count mismatch")
        if not valid_https(item["url"]):
            errors.append("manifest raw source URL must be valid anonymous HTTPS")
    if len(registry) < 3:
        errors.append("source registry is unexpectedly short")
    registry_ids = [row["source_id"] for row in registry]
    if any(not source for source in registry_ids) or len(set(registry_ids)) != len(registry_ids):
        errors.append("source registry IDs must be nonempty and unique")
    for row in registry:
        if row["retrieved"] != "2026-09-28" or not valid_https(row["url"]):
            errors.append(f"source registry invalid record: {row['source_id']}")
        if any(not row[field].strip() for field in ("title", "publisher", "role", "license")):
            errors.append(f"source registry missing provenance: {row['source_id']}")
    return errors


def check_other_layers(rows: list[dict[str, str]], paths: list[Path]) -> list[str]:
    """Require readable prior layers and disjoint stable IDs, without changing them."""
    if not paths:
        return ["at least one prior layer is required for stable-ID checking"]
    errors: list[str] = []
    ids = {row["stable_id"] for row in rows}
    for path in paths:
        other_rows = read_tsv(path, FIELDS)
        other_ids = Counter(row["stable_id"] for row in other_rows)
        if any(not key or count != 1 for key, count in other_ids.items()):
            errors.append(f"prior layer has duplicate/empty IDs: {path}")
        overlap = ids.intersection(other_ids)
        if overlap:
            errors.append(f"stable IDs overlap {path}: {sorted(overlap)[:3]}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Validate read-only UK tables, cross-layer identity and native reproducibility."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--other-layer", type=Path, action="append")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        rows = read_tsv(args.data, FIELDS)
        errors = validate_records(
            rows,
            read_tsv(args.snapshot, SNAPSHOT_FIELDS),
            read_tsv(args.manifest, MANIFEST_FIELDS),
            read_tsv(args.registry, REGISTRY_FIELDS),
        )
        errors.extend(check_other_layers(rows, args.other_layer or list(OTHER_LAYERS)))
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
        "PASS: 722 licensed UK facility records; deterministic rebuild; no inferred reactors, capacity, status, or coordinates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
