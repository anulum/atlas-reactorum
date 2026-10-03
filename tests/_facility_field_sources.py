# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete original facility-field test inputs

"""Copy every genuine reviewed input and make explicit negative mutations only."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import mapping

ROOT = Path(__file__).resolve().parents[1]
PINS = "metadata/facility_fields/source_pins.json"


def document(path: Path) -> dict[str, object]:
    """Read one native JSON object without converting its original scalar values."""
    return mapping(json.loads(path.read_bytes()))


def specification(root: Path, key: str, *, target: bool = False) -> dict[str, object]:
    """Read a copied source or target binding from the complete original ledger."""
    pins = document(root / PINS)
    return mapping(mapping(pins["target_datasets" if target else "sources"])[key])


def replace_input(root: Path, key: str, body: bytes, *, target: bool = False) -> None:
    """Damage one complete owned copy and update only that copy's digest."""
    pins = document(root / PINS)
    item = mapping(mapping(pins["target_datasets" if target else "sources"])[key])
    (root / str(item["path"])).write_bytes(body)
    item["sha256"] = hashlib.sha256(body).hexdigest()
    (root / PINS).write_text(json.dumps(pins, ensure_ascii=False, indent=2) + "\n")


def table(root: Path, key: str, *, target: bool = False) -> list[dict[str, str]]:
    """Read the entire real table selected by an original copied binding."""
    item = specification(root, key, target=target)
    with (root / str(item["path"])).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream, delimiter="," if key == "wri" and not target else "\t"))


def replace_table(
    root: Path, key: str, rows: list[dict[str, str]], *, target: bool = False
) -> None:
    """Write an explicitly damaged complete table into its owned copy only."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, list(rows[0]), delimiter="," if key == "wri" and not target else "\t"
    )
    writer.writeheader()
    writer.writerows(rows)
    replace_input(root, key, stream.getvalue().encode(), target=target)


def run_cli(
    module: str, root: Path, *args: str, optimize: bool = False
) -> subprocess.CompletedProcess[str]:
    """Exercise the real producer or validator from an unrelated working directory."""
    return subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimize else []),
            str(ROOT / "metadata/facility_fields" / (module + ".py")),
            "--source-root",
            str(root),
            *args,
        ],
        cwd=root.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.fixture
def original_source(tmp_path: Path) -> Path:
    """Copy all ten complete sources, four complete target tables and original pins."""
    root = tmp_path / "originals"
    pins = document(ROOT / PINS)
    paths = [PINS]
    for section in ("sources", "target_datasets"):
        paths.extend(str(mapping(item)["path"]) for item in mapping(pins[section]).values())
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return root
