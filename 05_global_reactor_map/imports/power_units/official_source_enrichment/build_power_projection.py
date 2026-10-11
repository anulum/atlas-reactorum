#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power-unit projection CLI
"""Build or validate the complete offline power-unit documentary projection."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_bundle import MEMBERS, load_projection, produce


def main(argv: list[str] | None = None) -> int:
    """Exercise the whole source-bound producer or release consumer through the CLI.

    Parameters
    ----------
    argv : list of str or None
        Explicit arguments for API callers; None reads the actual process arguments.

    Returns
    -------
    int
        Zero for a whole admitted bundle, one for a refused input or output.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="original frozen power-unit TSV")
    parser.add_argument("directory", type=Path, help="whole source/field/projection bundle")
    parser.add_argument("--check", action="store_true", help="verify the existing product")
    arguments = parser.parse_args(argv)
    try:
        if arguments.check:
            projection = load_projection(arguments.source, arguments.directory)
            if projection is None:
                raise ValueError("power bundle is absent")
        else:
            projection, document = produce(arguments.source, arguments.directory)
            destination = arguments.directory / MEMBERS[2]
            if destination.is_symlink():
                raise ValueError("power projection output cannot be a symlink")
            destination.write_text(
                json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
    except (OSError, ValueError, UnicodeError, csv.Error) as error:
        print(f"POWER PROJECTION REFUSED: {error}", file=sys.stderr)
        return 1
    selected = sum(row["disposition"] == "qualified" for row in projection.decisions)
    print(
        f"POWER PROJECTION ACCEPTED: {len(projection.rows)} rows, {len(projection.decisions)} decisions, {selected} qualified fields"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
