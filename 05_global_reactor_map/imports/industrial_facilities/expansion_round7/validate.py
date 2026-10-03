# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — read-only industrial round7 field parity
"""Verify every consumer cell against the complete immutable source snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .artifacts import BUNDLE_MANIFEST, DATASET_NAME, SNAPSHOT_NAME, SOURCE_MANIFEST, read_bundle
from .contracts import FIELDS, HERE, SNAPSHOT_FIELDS, ImportRefused, read_table
from .provenance import freeze_captures
from .records import project_rows

OTHER_LAYERS = (
    HERE.parent / "industrial_facilities.tsv",
    *(HERE.parent / f"expansion_round{n}/industrial_facilities_round{n}.tsv" for n in range(2, 7)),
)
BUNDLE_FILES = (
    SNAPSHOT_NAME,
    DATASET_NAME,
    SOURCE_MANIFEST,
    "source_registry.tsv",
    "source_snapshot_manifest.tsv",
    "RIGHTS.md",
    BUNDLE_MANIFEST,
)


def validate(
    snapshot: Path, dataset: Path, *, previous_layers: tuple[Path, ...] = OTHER_LAYERS
) -> int:
    """Check all fields and cross-layer identity collisions without any writes.

    Parameters
    ----------
    snapshot, dataset : pathlib.Path
        Full original-cell source table and complete 18-field consumer product.
    previous_layers : tuple of pathlib.Path
        Earlier accepted layers whose stable identities must remain disjoint.

    Returns
    -------
    int
        Number of source-parity discovery records.

    Raises
    ------
    ImportRefused
        A table, field, order, count or cross-layer identity fails its contract.
    OSError
        A requested input cannot be read.
    """
    expected = project_rows(read_table(snapshot, SNAPSHOT_FIELDS))
    actual = read_table(dataset, FIELDS)
    if actual != expected:
        raise ImportRefused("dataset differs from its complete source-cell projection")
    earlier: set[str] = set()
    for path in previous_layers:
        for row in read_table(path, FIELDS):
            identity = row["stable_id"].casefold()
            if not identity.strip() or identity in earlier:
                raise ImportRefused("previous-layer identity is empty or duplicated")
            earlier.add(identity)
    if earlier.intersection(row["stable_id"].casefold() for row in actual):
        raise ImportRefused("round7 identity collides with an earlier accepted layer")
    return len(actual)


def validate_bundle(
    directory: Path,
    *,
    capture_directory: Path | None = None,
    previous_layers: tuple[Path, ...] = OTHER_LAYERS,
) -> int:
    """Verify all provenance, rights and products, optionally against original custody.

    Parameters
    ----------
    directory : pathlib.Path
        Complete frozen bundle with all seven bound artifacts.
    capture_directory : pathlib.Path, optional
        Complete original raw resources and receipts for fresh source-cell parity.
    previous_layers : tuple of pathlib.Path
        Earlier layers actually present in the source tree being integrated.

    Returns
    -------
    int
        Number of source-bound discovery records, disjoint from prior layers.

    Raises
    ------
    ImportRefused
        Any artifact, original source binding or cross-layer identity differs.
    OSError
        An input cannot be read.
    """
    snapshot, manifest, _ = read_bundle(directory)
    if capture_directory is not None:
        original_snapshot, original_manifest = freeze_captures(capture_directory)
        if (snapshot, manifest) != (original_snapshot, original_manifest):
            raise ImportRefused("bundle differs from its complete original raw custody")
    return validate(
        directory / SNAPSHOT_NAME, directory / DATASET_NAME, previous_layers=previous_layers
    )


def validate_optional_bundle(
    directory: Path, *, previous_layers: tuple[Path, ...] = OTHER_LAYERS
) -> None:
    """Allow an absent layer, refusing any incomplete or altered frozen bundle.

    Parameters
    ----------
    directory : pathlib.Path
        Source directory that may contain a complete round-seven bundle.
    previous_layers : tuple of pathlib.Path
        Earlier layers actually present in the integrated source tree.

    Raises
    ------
    ImportRefused
        A present artifact does not belong to a complete valid source bundle.
    OSError
        A required source artifact cannot be read.
    """
    if any((directory / name).exists() or (directory / name).is_symlink() for name in BUNDLE_FILES):
        validate_bundle(directory, previous_layers=previous_layers)


def main() -> None:
    """Validate complete field parity against the canonical previous layers."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--snapshot", type=Path)
    modes.add_argument("--directory", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--capture-directory", type=Path)
    args = parser.parse_args()
    if args.directory is not None and args.dataset is not None:
        parser.error("--dataset belongs to --snapshot mode")
    if args.directory is None and (args.dataset is None or args.capture_directory is not None):
        parser.error("--snapshot requires --dataset; raw custody checking requires --directory")
    try:
        count = (
            validate_bundle(args.directory, capture_directory=args.capture_directory)
            if args.directory is not None
            else validate(args.snapshot, args.dataset)
        )
    except (OSError, ImportRefused):
        print("INDUSTRIAL VALIDATION FAILED: source parity or layer identity differs")
        raise SystemExit(1) from None
    print(
        f"{count} discovery records match all source fields; "
        "raw custody, source rights and physical verification remain separate checks"
    )


if __name__ == "__main__":
    main()
