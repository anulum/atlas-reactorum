# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — catalogue CLI test inputs

"""Copy checked-in catalogues and execute their real command-line tools."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a checked-in table with its original column order."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"Table has no header: {path}")
        return list(reader.fieldnames), list(reader)


def write_table(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    """Serialize a table copy after an explicit test mutation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def run_cli(
    script: Path, *arguments: str, cwd: Path | None = None, optimize: bool = False
) -> subprocess.CompletedProcess[str]:
    """Execute the actual repository script with bounded process lifetime."""
    return subprocess.run(
        [sys.executable, *(["-O"] if optimize else []), str(script), *arguments],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
