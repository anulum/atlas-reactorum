#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round8/build.py
"""Generate dated company-depth8 products from frozen reviewed metadata."""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from metadata.company_audit.depth_round8.review import (
    HERE,
    REVIEW_FIELDS,
    gap_reviews,
    load_review,
)
from metadata.company_audit.depth_round8.tables import BINDING_FIELDS, PROFILE_FIELDS, SOURCE_FIELDS

PRODUCT_NAMES = (
    "enrichment_overlays.tsv",
    "source_registry.tsv",
    "field_source_bindings.tsv",
    "gap_review.tsv",
)


def protect_outputs(paths: list[Path], inputs: tuple[Path, ...]) -> None:
    """Refuse output aliases of source inputs, symlinks and nonregular targets.

    Parameters
    ----------
    paths : list of pathlib.Path
        Complete prospective output set, before any filesystem write.
    inputs : tuple of pathlib.Path
        Reviewed, matrix and historical source files.

    Raises
    ------
    ValueError
        A target would replace a source or is not an owned regular output.
    """
    protected = {path.resolve() for path in inputs}
    for path in paths:
        if path.resolve() in protected:
            raise ValueError("output would replace a source input")
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError("output is a symlink or nonregular target")


def main() -> None:
    """Validate the complete input set before staging deterministic TSV products."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-directory", type=Path, default=HERE / "reviewed_inputs")
    parser.add_argument(
        "--gap-matrix", type=Path, default=HERE.parent / "depth_round4/gap_matrix.tsv"
    )
    parser.add_argument("--history-directory", type=Path, default=HERE.parent)
    parser.add_argument("--output-directory", type=Path, default=HERE)
    args = parser.parse_args()
    try:
        review = load_review(args.input_directory, args.gap_matrix, args.history_directory)
        reviews = gap_reviews(review)
        products = (
            (PROFILE_FIELDS, review.profiles),
            (SOURCE_FIELDS, review.sources),
            (BINDING_FIELDS, review.bindings),
            (REVIEW_FIELDS, reviews),
        )
        targets = [args.output_directory / name for name in PRODUCT_NAMES]
        protect_outputs(targets, review.inputs)
        args.output_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".depth8-", dir=args.output_directory) as temporary:
            stage = Path(temporary)
            for name, (fields, rows) in zip(PRODUCT_NAMES, products, strict=True):
                with (stage / name).open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(
                        handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
                    )
                    writer.writeheader()
                    writer.writerows(rows)
            for name, target in zip(PRODUCT_NAMES, targets, strict=True):
                os.replace(stage / name, target)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(
        f"{len(review.profiles)} overlays, {len(review.sources)} sources, {len(review.bindings)} field associations; reviewed {sum(int(row['metadata_fields_reviewed']) for row in reviews)} metadata gap fields; physical closure not established"
    )


if __name__ == "__main__":
    main()
