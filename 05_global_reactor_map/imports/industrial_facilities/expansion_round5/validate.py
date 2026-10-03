#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round5/validate.py
"""Validate round-five process-specific industrial discovery records."""

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
DATA = ROOT / "industrial_facilities_round5.tsv"
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
REGISTRY = ROOT / "source_registry.tsv"
MATRIX = ROOT / "source_gap_matrix.tsv"
EXPECTED = {"uk-repd-ad": 362, "fr-ademe-h2": 31}
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
    "source_row_id",
    "facility_name",
    "operator",
    "country",
    "region_or_commune",
    "lat",
    "lon",
    "coordinate_basis",
    "source_x",
    "source_y",
    "technology_type",
    "process_detail",
    "status",
    "capacity",
    "project_name",
    "source_record_updated",
]
MATRIX_FIELDS = [
    "source_id",
    "process_theme",
    "jurisdiction",
    "official_source",
    "official_url",
    "scope",
    "years_or_update",
    "coordinate_availability",
    "explicit_process_or_technology",
    "license_or_reuse_status",
    "access_mechanism",
    "systematic_selection",
    "import_decision",
    "evidence_notes",
    "retrieved",
]


MANIFEST_FIELDS = ["source", "url", "retrieved", "bytes", "sha256", "raw_rows", "selected_rows"]
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
    ROOT.parent / "expansion_round3/industrial_facilities_round3.tsv",
    ROOT.parent / "expansion_round4/industrial_facilities_round4.tsv",
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
    matrix: list[dict[str, str]],
) -> list[str]:
    """Check all accepted project facts, source provenance and process-gap decisions."""
    for records, fields in (
        (rows, FIELDS),
        (snapshot, SNAPSHOT_FIELDS),
        (manifest, MANIFEST_FIELDS),
        (registry, REGISTRY_FIELDS),
        (matrix, MATRIX_FIELDS),
    ):
        if any(
            set(row) != set(fields) or any(not isinstance(v, str) for v in row.values())
            for row in records
        ):
            return ["record differs from its required string schema"]
    errors: list[str] = []
    if len(rows) != 393 or len(snapshot) != 393:
        errors.append(f"expected 393 output/snapshot rows; got {len(rows)}/{len(snapshot)}")
    if Counter(row["source"] for row in snapshot) != Counter(EXPECTED):
        errors.append(
            f"unexpected snapshot source counts: {Counter(row['source'] for row in snapshot)}"
        )

    matrix_ids = [row["source_id"] for row in matrix]
    if any(not source for source in matrix_ids) or len(set(matrix_ids)) != len(matrix_ids):
        errors.append("matrix source IDs must be nonempty and unique")
    imports = {row["source_id"] for row in matrix if row["import_decision"].startswith("IMPORT")}
    if imports != set(EXPECTED):
        errors.append(f"matrix import decisions do not match built sources: {imports}")
    themes = {row["process_theme"] for row in matrix}
    for required_theme in (
        "anaerobic digestion / biogas",
        "hydrogen production",
        "wastewater treatment",
        "refining",
        "gasification / ammonia",
        "fermentation",
    ):
        if required_theme not in themes:
            errors.append(f"matrix missing process theme: {required_theme}")
    for row in matrix:
        if row["retrieved"] != "2026-09-28" or not valid_https(row["official_url"]):
            errors.append(f"invalid matrix provenance for {row['source_id']}")

    ids = Counter(row["stable_id"] for row in rows)
    if any(not key or count != 1 for key, count in ids.items()):
        errors.append("stable IDs must be non-empty and unique")
    snapshot_keys = Counter((row["source"], row["source_record_id"]) for row in snapshot)
    if any(not key[1] or count != 1 for key, count in snapshot_keys.items()):
        errors.append("snapshot source keys must be non-empty and unique")
    expected_ids = {
        (
            ("uk-repd:" if row["source"] == "uk-repd-ad" else "fr-ademe-h2:")
            + row["source_record_id"]
        )
        for row in snapshot
    }
    if set(ids) != expected_ids:
        errors.append("output stable IDs do not match snapshot source keys")

    required = (
        "facility_name",
        "country",
        "lat",
        "lon",
        "precision",
        "sector",
        "process_or_activity",
        "status",
        "operator",
        "pollutant_or_product_context",
        "source_url",
        "source_role",
        "retrieved",
        "license",
        "verification_notes",
    )
    for row in rows:
        key = row["stable_id"]
        for field in required:
            if not row[field].strip():
                errors.append(f"{key}: missing {field}")
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                errors.append(f"{key}: coordinate out of range")
        except ValueError:
            errors.append(f"{key}: non-numeric coordinate")
        if row["retrieved"] != "2026-09-28" or not valid_https(row["source_url"]):
            errors.append(f"{key}: invalid retrieval/source URL")
        if "not independently verified" not in row["status"]:
            errors.append(f"{key}: source status caveat missing")
        if key.startswith("uk-repd:"):
            if (
                row["country"] != "United Kingdom"
                or "source technology type" not in row["reactor_type_if_explicit"]
            ):
                errors.append(f"{key}: UK technology/country mismatch")
        elif key.startswith("fr-ademe-h2:"):
            if row["country"] != "France" or row["reactor_type_if_explicit"]:
                errors.append(f"{key}: ADEME reactor type must remain blank")
        else:
            errors.append(f"{key}: unexpected stable-ID prefix")

    for src in snapshot:
        if src["source"] == "uk-repd-ad":
            if src["technology_type"] != "Anaerobic Digestion" or src["region_or_commune"] not in {
                "England",
                "Scotland",
                "Wales",
            }:
                errors.append(f"{src['source_record_id']}: UK selection rule mismatch")
            try:
                east, north = float(src["source_x"]), float(src["source_y"])
                if not 0 <= east <= 700000 or not 0 <= north <= 1300000:
                    errors.append(f"{src['source_record_id']}: implausible BNG point")
            except ValueError:
                errors.append(f"{src['source_record_id']}: invalid BNG point")
        elif src["source"] == "fr-ademe-h2":
            if (
                src["technology_type"] != "Hydrogen production"
                or src["process_detail"] != "ADEME site type: Production"
            ):
                errors.append(f"{src['source_record_id']}: ADEME selection rule mismatch")

    if {row["source"] for row in manifest} != set(EXPECTED) or len(manifest) != 2:
        errors.append("manifest must contain exactly the two imported sources")
    for row in manifest:
        source = row["source"]
        digest = row["sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"invalid manifest hash for {source}")
        try:
            if (
                row["retrieved"] != "2026-09-28"
                or int(row["selected_rows"]) != EXPECTED.get(source)
                or int(row["bytes"]) <= 0
                or int(row["raw_rows"]) < int(row["selected_rows"])
            ):
                raise ValueError("invalid counts/date")
        except ValueError:
            errors.append(f"manifest count/date mismatch for {source}")
        if not valid_https(row["url"]):
            errors.append(f"manifest URL must be valid anonymous HTTPS for {source}")
    if len(registry) < 6:
        errors.append("source registry is unexpectedly short")
    source_ids = [row["source_id"] for row in registry]
    if any(not source for source in source_ids) or len(set(source_ids)) != len(source_ids):
        errors.append("source registry IDs must be nonempty and unique")
    for row in registry:
        if row["retrieved"] != "2026-09-28" or not valid_https(row["url"]):
            errors.append(f"invalid source registry row: {row['source_id']}")
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
    """Validate read-only historical tables and the actual corrected producer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
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
            read_tsv(args.matrix, MATRIX_FIELDS),
        )
        errors.extend(check_other_layers(rows, list(args.other_layer or OTHER_LAYERS)))
        if not errors and not verify_rebuild(args.data, args.snapshot, timeout=args.timeout):
            errors.append("offline rebuild is not deterministic")
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print("FAIL")
        for error in errors:
            print("-", error)
        return 1
    print(
        "PASS: 393 process-specific records from two reusable official sources; deterministic and no inferred vessel/status claims"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
