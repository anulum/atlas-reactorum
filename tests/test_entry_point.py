# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_entry_point.py

"""Tests that each build script actually runs when invoked as a script.

Importing a module and calling ``main()`` does not prove the file works as a
command. A refactor once moved ``main`` below its ``if __name__`` guard, so the
script exited with a ``NameError`` and wrote nothing — while a checksum
comparison against the already-correct files on disk still reported success.

That is the path-filter false-green class: a check that never ran was read as a
check that passed. These tests close the hole at the mechanism by executing the
scripts as subprocesses and requiring them to produce output, so a build that
does not run can never look like a build that succeeded.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "04_interactive_presentation" / "data"

SCRIPTS = [
    ROOT / "04_interactive_presentation" / "scripts" / "build_datasets.py",
    ROOT / "metadata" / "coverage_audit" / "build_coverage.py",
]


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_exits_cleanly_when_run_as_a_command(script: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert result.returncode == 0, f"{script.name} failed:\n{result.stderr[-2000:]}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_defines_main_before_its_entry_point_guard(script: Path) -> None:
    # A guard placed above the definition raises NameError at run time while
    # every import-based test still passes.
    source = script.read_text(encoding="utf-8")
    guard = source.rindex('if __name__ == "__main__":')
    definition = source.index("def main(")
    assert definition < guard, f"{script.name} calls main() before defining it"


def test_rebuilding_a_deleted_output_actually_regenerates_it() -> None:
    # The decisive check: remove a published artefact and require the script to
    # recreate it byte for byte. A script that silently does nothing fails here,
    # where a plain checksum comparison would still have passed.
    target = DATA / "global_reactors.sample.json"
    original = target.read_bytes()
    backup = target.with_suffix(".json.entrypointtest")
    shutil.copy2(target, backup)
    try:
        target.unlink()
        result = subprocess.run(
            [sys.executable, str(SCRIPTS[0])],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        assert result.returncode == 0, result.stderr[-2000:]
        assert target.is_file(), "the builder did not recreate the deleted output"
        assert target.read_bytes() == original, "rebuild did not reproduce the published bytes"
    finally:
        if not target.is_file():
            shutil.copy2(backup, target)
        backup.unlink(missing_ok=True)
