#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round6/validate.py
"""Validate round-six industrial facility discovery artifacts."""

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
DATA = ROOT / "industrial_facilities_round6.tsv"
SNAPSHOT = ROOT / "selected_source_snapshot.tsv"
MANIFEST = ROOT / "source_snapshot_manifest.tsv"
REGISTRY = ROOT / "source_registry.tsv"
MATRIX = ROOT / "source_gap_matrix.tsv"
RIGHTS = ROOT / "RIGHTS.md"
EXPECTED = {
    "br-epe-ethanol": 431,
    "br-epe-biodiesel": 88,
    "br-epe-biomethane": 70,
    "us-epa-lmop": 542,
}
PREFIX = {
    "br-epe-ethanol": "br-epe-ethanol:",
    "br-epe-biodiesel": "br-epe-biodiesel:",
    "br-epe-biomethane": "br-epe-biomethane:",
    "us-epa-lmop": "us-epa-lmop:",
}
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
    "country",
    "subdivision",
    "municipality_or_county",
    "lat",
    "lon",
    "coordinate_basis",
    "plant_or_project_type",
    "source_status",
    "operator_or_parties",
    "capacity",
    "feedstock_or_context",
    "start_date",
    "source_row_notes",
]
MATRIX_FIELDS = [
    "source_id",
    "process_theme",
    "jurisdiction",
    "official_source",
    "official_url",
    "scope",
    "coordinate_availability",
    "technology_or_process_fields",
    "rights_status",
    "access_mechanism",
    "systematic_selection",
    "import_decision",
    "rationale",
    "retrieved",
]


MANIFEST_FIELDS = [
    "source",
    "title",
    "url",
    "retrieved",
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
    *(ROOT.parent / f"expansion_round{n}/industrial_facilities_round{n}.tsv" for n in range(2, 6)),
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
    """Check source-key joins, observations, provenance and complete gap decisions."""
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
    if len(rows) != 1131 or len(snapshot) != 1131:
        errors.append(f"expected 1,131 output/snapshot rows; got {len(rows)}/{len(snapshot)}")
    actual_counts = Counter(row["source"] for row in snapshot)
    if actual_counts != Counter(EXPECTED):
        errors.append(f"unexpected source counts: {actual_counts}")

    matrix_ids = [row["source_id"] for row in matrix]
    if any(not key for key in matrix_ids) or len(set(matrix_ids)) != len(matrix_ids):
        errors.append("matrix source IDs must be nonempty and unique")
    imports = {row["source_id"] for row in matrix if row["import_decision"].startswith("IMPORT")}
    if imports != set(EXPECTED):
        errors.append(f"matrix imports do not match built sources: {imports}")
    themes = " ".join(row["process_theme"].lower() for row in matrix)
    for theme in (
        "ethanol",
        "biodiesel",
        "biomethane",
        "landfill gas",
        "hydrogen",
        "gasification",
        "refining",
    ):
        if theme not in themes:
            errors.append(f"gap matrix lacks theme: {theme}")
    for row in matrix:
        if row["retrieved"] != "2026-09-28" or not valid_https(row["official_url"]):
            errors.append(f"invalid matrix provenance for {row['source_id']}")
        if not row["rights_status"] or not row["import_decision"]:
            errors.append(f"incomplete matrix decision for {row['source_id']}")

    ids = Counter(row["stable_id"] for row in rows)
    if any(not key or count != 1 for key, count in ids.items()):
        errors.append("stable IDs must be non-empty and unique")
    source_keys = Counter((row["source"], row["source_record_id"]) for row in snapshot)
    if any(not key[1] or count != 1 for key, count in source_keys.items()):
        errors.append("snapshot source keys must be non-empty and unique")
    source_row_keys = Counter((row["source"], row["source_row_id"]) for row in snapshot)
    if any(not key[1] or count != 1 for key, count in source_row_keys.items()):
        errors.append("snapshot service row IDs must be non-empty and unique")
    expected_ids = {
        PREFIX.get(row["source"], "unknown:") + row["source_record_id"] for row in snapshot
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
            if row["country"] == "Brazil" and not (-35 <= lat <= 6 and -75 <= lon <= -30):
                errors.append(f"{key}: coordinate outside broad Brazil bounds")
            if row["country"] == "United States" and not (-170 <= lon <= -60 and 15 <= lat <= 75):
                errors.append(f"{key}: coordinate outside broad US bounds")
        except ValueError:
            errors.append(f"{key}: invalid coordinate")
        if row["retrieved"] != "2026-09-28" or not valid_https(row["source_url"]):
            errors.append(f"{key}: invalid source/date")
        if row["reactor_type_if_explicit"]:
            errors.append(f"{key}: reactor field must remain blank")
        if "not independently verified" not in row["status"]:
            errors.append(f"{key}: status caveat missing")
        if key.startswith("br-epe-"):
            if (
                row["country"] != "Brazil"
                or row["license"] != "Creative Commons Attribution 4.0 International"
            ):
                errors.append(f"{key}: EPE country/licence mismatch")
            if (
                "No fermentation, digestion, upgrading, reactor or vessel design is inferred"
                not in row["verification_notes"]
            ):
                errors.append(f"{key}: EPE non-inference caveat missing")
        elif key.startswith("us-epa-lmop:"):
            if row["country"] != "United States" or "CC0" not in row["license"]:
                errors.append(f"{key}: LMOP country/licence mismatch")
            if "not mislabelled as a reactor type" not in row["verification_notes"]:
                errors.append(f"{key}: LMOP technology caveat missing")
        else:
            errors.append(f"{key}: unexpected stable-ID prefix")

    for src in snapshot:
        for field in (
            "facility_name",
            "country",
            "subdivision",
            "municipality_or_county",
            "lat",
            "lon",
            "coordinate_basis",
            "plant_or_project_type",
            "source_status",
            "operator_or_parties",
            "feedstock_or_context",
            "source_row_notes",
        ):
            if not src[field].strip():
                errors.append(f"snapshot is missing {field}")
        try:
            lat, lon = float(src["lat"]), float(src["lon"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError("invalid WGS84 point")
        except ValueError:
            errors.append("snapshot has invalid coordinates")
        key = f"{src['source']}:{src['source_record_id']}"
        if src["country"] == "Brazil":
            if src["source"] not in {"br-epe-ethanol", "br-epe-biodiesel", "br-epe-biomethane"}:
                errors.append(f"{key}: unexpected Brazil source")
            if "EPE-published" not in src["coordinate_basis"]:
                errors.append(f"{key}: EPE coordinate provenance missing")
        elif src["country"] == "United States":
            if src["source"] != "us-epa-lmop" or not src["source_status"].startswith(
                "Operational landfill-gas energy project"
            ):
                errors.append(f"{key}: LMOP scope mismatch")
            if "EPA LMOP-published" not in src["coordinate_basis"]:
                errors.append(f"{key}: LMOP coordinate provenance missing")
        else:
            errors.append(f"{key}: unexpected country")

    if len(manifest) != 4 or {row["source"] for row in manifest} != set(EXPECTED):
        errors.append("manifest must contain exactly four imported sources")
    for row in manifest:
        source, digest = row["source"], row["sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"invalid manifest hash for {source}")
        try:
            if (
                row["retrieved"] != "2026-09-28"
                or int(row["selected_rows"]) != EXPECTED.get(source)
                or int(row["bytes"]) <= 0
                or row["raw_rows"] != row["selected_rows"]
            ):
                raise ValueError("invalid complete-layer counts/date")
        except ValueError:
            errors.append(f"manifest count/date mismatch for {source}")
        if not row["title"].strip() or not valid_https(row["url"]):
            errors.append(f"manifest lacks title/anonymous HTTPS for {source}")
    if len(registry) < 12:
        errors.append("source registry is unexpectedly short")
    registry_ids = [row["source_id"] for row in registry]
    if any(not key for key in registry_ids) or len(set(registry_ids)) != len(registry_ids):
        errors.append("source registry IDs must be nonempty and unique")
    for row in registry:
        if row["retrieved"] != "2026-09-28" or not valid_https(row["url"]):
            errors.append(f"invalid source registry row: {row['source_id']}")
        if any(not row[field].strip() for field in ("title", "publisher", "role", "license")):
            errors.append(f"source registry missing provenance: {row['source_id']}")
    return errors


def validate_rights(text: str) -> list[str]:
    """Require the retained rights statement without widening its stated scope."""
    return [
        f"RIGHTS.md lacks: {phrase}"
        for phrase in (
            "Creative Commons Attribution 4.0 International",
            "CC0 1.0",
            "Boundary of this rights review",
        )
        if phrase not in text
    ]


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
    """Validate read-only tables, rights and all prior layers with an isolated rebuild."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--rights", type=Path, default=RIGHTS)
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
        errors.extend(validate_rights(args.rights.read_text(encoding="utf-8")))
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
        "PASS: 1,131 reusable official biofuel and landfill-gas project records; deterministic and no inferred reactors/coordinates/status"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
