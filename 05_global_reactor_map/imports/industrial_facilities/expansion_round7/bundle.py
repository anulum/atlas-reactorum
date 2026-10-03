# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete offline industrial source bundle
"""Create complete protected source bundles from verified custody or frozen artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .artifacts import bundle_schema_version, expected_artifacts, read_bundle
from .build_dataset import checked_destination, write_output
from .capture import read_captures
from .contracts import ImportRefused
from .provenance import freeze_captures


def create_bundle(
    source: Path, output: Path, *, frozen: bool = False, upgrade_provenance: bool = False
) -> int:
    """Publish all seven artifacts into a new external directory without replacement.

    Parameters
    ----------
    source, output : pathlib.Path
        Complete raw custody or frozen bundle, and a new external destination.
    frozen : bool
        Rebuild only from verified frozen artifacts, with no network acquisition.
    upgrade_provenance : bool
        Explicitly migrate a frozen version-one report and inventory to version
        two. Ordinary frozen reproduction retains all original artifact bytes.

    Returns
    -------
    int
        Number of source-derived facility discovery records.

    Raises
    ------
    ImportRefused
        Destination aliases source history, a source/artifact contract differs,
        or a provenance upgrade was requested without frozen input.
    OSError
        A native file operation fails; partial owned output is preserved.
    """
    if upgrade_provenance and not frozen:
        raise ImportRefused("provenance upgrade requires a frozen bundle")
    target = checked_destination(output, (source,))
    if target.is_relative_to(source.resolve()):
        raise ImportRefused("bundle output must be separate from the immutable source tree")
    if frozen:
        snapshot, manifest, observations = read_bundle(source)
    else:
        snapshot, manifest = freeze_captures(source)
        observations, _ = read_captures(source)
    version = bundle_schema_version(source) if frozen and not upgrade_provenance else 2
    artifacts = expected_artifacts(snapshot, manifest, observations, schema_version=version)
    target.mkdir()
    for name, body in artifacts.items():
        write_output(target / name, body, inputs=(source,))
    read_bundle(target)
    return len(observations)


def main() -> None:
    """Run capture conversion or exact offline bundle reproduction through the native CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--capture-directory", type=Path)
    inputs.add_argument("--frozen-directory", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--upgrade-provenance",
        action="store_true",
        help="migrate a verified frozen report and inventory to bundle version 2",
    )
    args = parser.parse_args()
    if args.upgrade_provenance and args.frozen_directory is None:
        parser.error("--upgrade-provenance requires --frozen-directory")
    try:
        count = create_bundle(
            args.frozen_directory or args.capture_directory,
            args.output_directory,
            frozen=args.frozen_directory is not None,
            upgrade_provenance=args.upgrade_provenance,
        )
    except (OSError, ImportRefused):
        print(
            "INDUSTRIAL BUNDLE FAILED: source provenance or protected output violates its contract"
        )
        raise SystemExit(1) from None
    print(f"{count} source-derived discovery records; complete seven-artifact bundle written")


if __name__ == "__main__":
    main()
