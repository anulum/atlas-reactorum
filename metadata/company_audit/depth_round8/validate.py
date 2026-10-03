#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round8/validate.py
"""Compare persisted depth8 metadata with the complete frozen reviewed inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from metadata.company_audit.depth_round8.build import PRODUCT_NAMES, protect_outputs
from metadata.company_audit.depth_round8.review import (
    DATE,
    HERE,
    REVIEW_FIELDS,
    gap_reviews,
    load_review,
)
from metadata.company_audit.depth_round8.tables import (
    BINDING_FIELDS,
    PROFILE_FIELDS,
    SOURCE_FIELDS,
    read_table,
)


def main() -> None:
    """Verify every persisted row without rebuilding or promoting scientific claims."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE)
    parser.add_argument("--input-directory", type=Path, default=HERE / "reviewed_inputs")
    parser.add_argument(
        "--gap-matrix", type=Path, default=HERE.parent / "depth_round4/gap_matrix.tsv"
    )
    parser.add_argument("--history-directory", type=Path, default=HERE.parent)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = args.report or args.directory / "validation.json"
    try:
        review = load_review(args.input_directory, args.gap_matrix, args.history_directory)
        reviews = gap_reviews(review)
        paths = [args.directory / name for name in PRODUCT_NAMES]
        protect_outputs([report_path], (*review.inputs, *paths))
        expected = (
            (PROFILE_FIELDS, review.profiles),
            (SOURCE_FIELDS, review.sources),
            (BINDING_FIELDS, review.bindings),
            (REVIEW_FIELDS, reviews),
        )
        errors = [
            f"{path.name}: differs from frozen reviewed metadata"
            for path, (fields, rows) in zip(paths, expected, strict=True)
            if read_table(path, fields) != rows
        ]
        report = {
            "audit_date": DATE,
            "valid": not errors,
            "overlay_count": len(review.profiles),
            "source_count": len(review.sources),
            "field_association_count": len(review.bindings),
            "gap_review_count": len(reviews),
            "metadata_gap_fields_reviewed": sum(
                int(row["metadata_fields_reviewed"]) for row in reviews
            ),
            "physical_gap_closure": "not established by structural validation",
            "evidence_acceptance": "source attribution and limitations preserved; no independent replication inferred",
            "errors": errors,
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"VALIDATION FAILED: {error}")
        raise SystemExit(1) from None
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
