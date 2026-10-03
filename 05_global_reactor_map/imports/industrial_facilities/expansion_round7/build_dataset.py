# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — deterministic industrial round7 dataset builder
"""Build facility discovery records offline into a new protected destination."""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .capture import REPOSITORY
from .contracts import FIELDS, MAX_BYTES, SNAPSHOT_FIELDS, ImportRefused, read_table
from .records import project_rows


def checked_destination(path: Path, inputs: tuple[Path, ...]) -> Path:
    """Require a new external file under an existing nonsymlink directory.

    Parameters
    ----------
    path : pathlib.Path
        Explicit caller-selected output, never an accepted historical file.
    inputs : tuple of pathlib.Path
        Immutable files used by this invocation.

    Returns
    -------
    pathlib.Path
        Absolute destination after source, ancestor and existing-file checks.

    Raises
    ------
    ImportRefused
        Output aliases a source/repository path, exists or has an unsafe parent.
    """
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ImportRefused("output path contains a symlink")
    target = absolute.resolve()
    if target.is_relative_to(REPOSITORY) or target in {source.resolve() for source in inputs}:
        raise ImportRefused("output aliases repository history or a source input")
    if target.exists() or not target.parent.is_dir():
        raise ImportRefused("output must be new and its parent must already be a directory")
    return target


def table_bytes(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    """Encode the complete ordered TSV contract with deterministic quoting.

    Parameters
    ----------
    fields : list of str
        Exact ordered header of the snapshot or consumer product.
    rows : list of dict
        Verbatim field values, including whitespace and zero quantities.

    Returns
    -------
    bytes
        UTF-8 table using LF row terminators and standard quoted TSV cells.

    Raises
    ------
    ImportRefused
        Encoded output exceeds the same bounded-file consumer contract.
    """
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    body = stream.getvalue().encode("utf-8")
    if len(body) > MAX_BYTES:
        raise ImportRefused("generated table exceeds its bounded-file contract")
    return body


def write_output(path: Path, body: bytes, *, inputs: tuple[Path, ...]) -> None:
    """Publish complete bytes atomically without replacing any existing file.

    Parameters
    ----------
    path : pathlib.Path
        New explicit external destination.
    body : bytes
        Fully validated product bytes.
    inputs : tuple of pathlib.Path
        Protected input paths.

    Raises
    ------
    ImportRefused
        Destination fails protection checks.
    OSError
        A native write/link fails, including a concurrent existing destination.
    """
    target = checked_destination(path, inputs)
    with tempfile.TemporaryDirectory(prefix=".industrial7-", dir=target.parent) as directory:
        temporary = Path(directory) / "product.tsv"
        temporary.write_bytes(body)
        os.link(temporary, target)


def build(snapshot: Path, output: Path) -> int:
    """Build the entire reviewed round offline without modifying its inputs.

    Parameters
    ----------
    snapshot, output : pathlib.Path
        Complete original-cell snapshot and new external product path.

    Returns
    -------
    int
        Number of complete source-derived discovery records.

    Raises
    ------
    ImportRefused
        Snapshot, source projection or destination fails its authored contract.
    OSError
        A native file operation fails.
    """
    checked_destination(output, (snapshot,))
    rows = read_table(snapshot, SNAPSHOT_FIELDS)
    records = project_rows(rows)
    write_output(output, table_bytes(FIELDS, records), inputs=(snapshot,))
    return len(records)


def main() -> None:
    """Run the native offline builder with explicit immutable input/output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        count = build(args.snapshot, args.output)
    except (OSError, ImportRefused):
        print("INDUSTRIAL BUILD FAILED: source or new output violates its contract")
        raise SystemExit(1) from None
    print(f"{count} facility discovery records built offline; physical verification not implied")


if __name__ == "__main__":
    main()
