# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete native FFI source qualification boundaries.
"""Preserve the exact native observer and refuse new or changed FFI source through real tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate
from .test_javascript_tools import ROOT, required_tool


@pytest.fixture
def ffi_candidate(tmp_path: Path) -> Path:
    """Create a real source/index candidate containing the complete qualified libc observer.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owning working-disk parent for the native FFI candidate.

    Returns
    -------
    pathlib.Path
        Exact real observer and gate source; no native checker is substituted.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    names = [
        "tools/ffi.cjs",
        "tools/source-files.cjs",
        "tests/test_facility_fields_build.py",
        ".gitignore",
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", *names], cwd=root, check=True, capture_output=True
    )
    return root


def run_ffi(
    root: Path, python: str | None = sys.executable, *, node: str = "node"
) -> subprocess.CompletedProcess[str]:
    """Run the public gate against actual native Ruff and original source diagnostics.

    Parameters
    ----------
    root : pathlib.Path
        Complete original or deliberately changed FFI candidate.
    python : str or None
        Real qualified interpreter, unavailable path or None to exercise the project default.
    node : str
        Actual native executable name/path, including a separately verified refused runtime.

    Returns
    -------
    subprocess.CompletedProcess of str
        Native process status/stdout/stderr within the owning deadline.
    """
    environment = dict(os.environ)
    if python is None:
        environment.pop("ATLAS_PYTHON", None)
    else:
        environment["ATLAS_PYTHON"] = python
    command = [required_tool(node), "tools/ffi.cjs"]
    return run_gate(
        root,
        command,
        ["tools/ffi.cjs", "tools/source-files.cjs"],
        environment,
        60,
    )


def test_complete_nonffi_public_source_qualifies(ffi_candidate: Path) -> None:
    """Run the actual native checker on complete unchanged source beside the qualified observer.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Actual source/gate/index containing an original public Python module without FFI.
    """
    source = ffi_candidate / "future" / "research_objects.py"
    source.parent.mkdir()
    source.write_bytes((ROOT / "tools/research_objects.py").read_bytes())
    result = run_ffi(ffi_candidate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_empty_python_discovery_refuses(ffi_candidate: Path) -> None:
    """Refuse an actual empty Python input set after indexed source removal.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Independent original candidate whose sole Python source is removed from files and index.
    """
    subprocess.run(
        [required_tool("git"), "rm", "--cached", "--", "tests/test_facility_fields_build.py"],
        cwd=ffi_candidate,
        check=True,
        capture_output=True,
    )
    (ffi_candidate / "tests/test_facility_fields_build.py").unlink()
    result = run_ffi(ffi_candidate)
    assert result.returncode != 0
    assert "no Python FFI source" in result.stderr


@pytest.mark.parametrize("damage", ["missing", "symlink"])
def test_indexed_python_source_cannot_disappear(ffi_candidate: Path, damage: str) -> None:
    """Refuse genuinely absent or linked indexed source before native tool execution.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Complete original candidate with its independent file index.
    damage : str
        Missing source or native filesystem link to the retained original file.
    """
    source = ffi_candidate / "tests/test_facility_fields_build.py"
    source.unlink()
    if damage == "symlink":
        source.symlink_to(ROOT / "tests/test_facility_fields_build.py")
    result = run_ffi(ffi_candidate)
    assert result.returncode != 0
    assert ("ENOENT" if damage == "missing" else "symlink") in result.stderr


def test_missing_default_native_interpreter_refuses(ffi_candidate: Path) -> None:
    """Exercise the unconfigured project-default interpreter and retain its actual launch refusal.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Actual original gate/source/index without a fabricated default Python executable.
    """
    result = run_ffi(ffi_candidate, None)
    assert result.returncode != 0
    assert ".venv/bin/python" in result.stderr and "ENOENT" in result.stderr


def test_exact_complete_native_observer_qualifies(ffi_candidate: Path) -> None:
    """Accept only the current complete inotify source whose real producer cohort is maintained.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Exact original qualified source and native gate.
    """
    result = run_ffi(ffi_candidate)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "statement",
    [
        "import ctypes",
        "import ctypes as native",
        "from ctypes import CDLL",
        "import cffi",
        "import ctypes  # noqa: TID251",
    ],
)
def test_new_ffi_root_cannot_inherit_existing_source_qualification(
    ffi_candidate: Path, statement: str
) -> None:
    """Refuse new native imports/aliases and ignore an attempted inline gate suppression.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Existing complete qualified observer and owning gate.
    statement : str
        New native binding declaration appended to a complete original public module.
    """
    source = ffi_candidate / "future" / "research_objects.py"
    source.parent.mkdir()
    source.write_bytes(
        (ROOT / "tools/research_objects.py").read_bytes() + ("\n" + statement + "\n").encode()
    )
    result = run_ffi(ffi_candidate)
    assert result.returncode != 0
    assert "TID251" in result.stdout + result.stderr
    assert "future/research_objects.py" in result.stdout + result.stderr


def test_changed_qualified_source_requires_fresh_native_evidence(ffi_candidate: Path) -> None:
    """A byte change to the complete qualified role invalidates its retained source binding.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Independent complete observer; accepted code and source evidence are untouched.
    """
    source = ffi_candidate / "tests/test_facility_fields_build.py"
    source.write_bytes(source.read_bytes() + b"\n# Deliberately changed source candidate.\n")
    result = run_ffi(ffi_candidate)
    assert result.returncode != 0
    assert "FFI source needs complete native qualification" in result.stderr


def test_missing_native_tool_and_invalid_source_refuse(ffi_candidate: Path) -> None:
    """Refuse unavailable native tooling and a real native parse error without accepting empty reports.

    Parameters
    ----------
    ffi_candidate : pathlib.Path
        Complete gate/source with explicitly changed interpreter and source controls.
    """
    missing = run_ffi(ffi_candidate, str(ffi_candidate / "unavailable-python"))
    assert missing.returncode != 0 and "ENOENT" in missing.stderr
    source = ffi_candidate / "future.py"
    source.write_bytes((ROOT / "tools/research_objects.py").read_bytes() + b"\nnot python !\n")
    invalid = run_ffi(ffi_candidate)
    assert invalid.returncode != 0
    assert "invalid-syntax" in invalid.stdout + invalid.stderr
