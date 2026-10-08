# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete notebook public native gate controls.
"""Exercise original notebooks and new-root refusals through real public native commands."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.rebuild import repository_files
from tools.research_objects import object_fields, object_rows

from ._native_gate_ranges import run_gate
from .test_javascript_tools import ROOT, required_tool

NOTEBOOK = Path("examples/research/comparison.ipynb")


@pytest.fixture
def notebook_candidate(tmp_path: Path) -> Path:
    """Copy the complete current public snapshot into an independent native Git candidate.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owning working-disk parent for actual source, products, kernel and index.

    Returns
    -------
    pathlib.Path
        Complete source and product bytes; no native checker or kernel is replaced.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    for source in repository_files(ROOT):
        target = root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", "."], cwd=root, check=True, capture_output=True
    )
    return root


def run_notebooks(
    root: Path, mode: str, *, python: str = sys.executable, make: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the public original orchestrator or its Make target with actual native tools.

    Parameters
    ----------
    root : pathlib.Path
        Independent complete candidate with its own source index.
    mode : str
        Static, execute or deliberately unsupported public mode.
    python : str
        Actual qualified interpreter or explicitly unavailable executable path.
    make : bool
        Whether to route through the ordinary developer Make target.

    Returns
    -------
    subprocess.CompletedProcess of str
        Native status and diagnostics after the finite source/kernel deadline.
    """
    command = [required_tool("node"), "tools/notebooks.cjs", mode]
    if make:
        target = "native-notebook-runtime" if mode == "execute" else "native-notebooks"
        command = [required_tool("make"), target, "VENV=" + str(Path(python).parent.parent)]
    return run_gate(
        root,
        command,
        ["tools/notebooks.cjs", "tools/source-files.cjs"],
        {**os.environ, "ATLAS_PYTHON": python},
        180,
    )


@pytest.mark.parametrize("make", [False, True])
def test_complete_original_notebook_and_new_root_qualify(
    notebook_candidate: Path, make: bool
) -> None:
    """Check both public paths and discover an untracked exact original notebook in a new root.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Actual accepted source and complete data snapshot.
    make : bool
        Public command or ordinary Make integration.
    """
    original = (notebook_candidate / NOTEBOOK).read_bytes()
    future = notebook_candidate / "future" / "comparison.ipynb"
    future.parent.mkdir()
    future.write_bytes(original)
    result = run_notebooks(notebook_candidate, "static", make=make)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count('"executed_code_cells": 0') == 2
    assert future.read_bytes() == original == (notebook_candidate / NOTEBOOK).read_bytes()


@pytest.mark.parametrize(
    "mutation,diagnostic",
    [
        ("syntax", "SyntaxError"),
        ("contract", "D103"),
        ("types", "incompatible type"),
        ("format", "would be reformatted"),
        ("kernel", "deliberate public kernel refusal"),
    ],
)
def test_new_notebook_root_reaches_each_owning_native_gate(
    notebook_candidate: Path, mutation: str, diagnostic: str
) -> None:
    """Refuse complete source mutations through admission, Ruff, MyPy and genuine Jupyter.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Complete original data/source snapshot and genuine installed tools.
    mutation : str
        Deliberate suffix to the final original Python cell; no successful result is fabricated.
    diagnostic : str
        Native diagnostic proving the selected owning checker or kernel was reached.
    """
    document = object_fields(json.loads((ROOT / NOTEBOOK).read_bytes()))
    rows = object_rows(document["cells"])
    cell = next(cell for cell in reversed(rows) if cell["cell_type"] == "code")
    source = cell["source"]
    assert isinstance(source, list) and all(isinstance(line, str) for line in source)
    suffix = {
        "syntax": "not python !\n",
        "contract": "\ndef undocumented_native_notebook(value: object) -> object:\n    return value\n",
        "types": "\nprint(len(17))\n",
        "format": "\nprint(  result_sha256  )\n",
        "kernel": '\nraise ValueError("deliberate public kernel refusal")\n',
    }[mutation]
    cell["source"] = [*source, suffix]
    document["cells"] = rows
    future = notebook_candidate / "future" / "comparison.ipynb"
    future.parent.mkdir()
    future.write_text(json.dumps(document))
    if mutation in {"types", "kernel"}:
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", str(future)],
            cwd=notebook_candidate,
            check=True,
            capture_output=True,
            timeout=30,
        )
    original = future.read_bytes()
    result = run_notebooks(
        notebook_candidate, "execute" if mutation == "kernel" else "static", make=True
    )
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr
    assert future.read_bytes() == original


def test_original_notebook_executes_through_public_gate(notebook_candidate: Path) -> None:
    """Run all five complete original cells in a genuine kernel and preserve exact accepted bytes.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Real accepted source, examples, declarations and source-bound products.
    """
    original = (notebook_candidate / NOTEBOOK).read_bytes()
    result = run_notebooks(notebook_candidate, "execute", make=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"executed_code_cells": 5' in result.stdout
    assert "Repeated restoration agrees: True" in result.stdout
    assert "Original statements retained: 11" in result.stdout
    assert "Missing numeric parameter records: 2" in result.stdout
    assert (notebook_candidate / NOTEBOOK).read_bytes() == original


def test_real_kernel_cannot_change_original_notebook_source(notebook_candidate: Path) -> None:
    """Refuse actual source mutation by a genuine kernel after otherwise complete original execution.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Complete original source/data snapshot; mutation affects only this owned candidate.
    """
    source = notebook_candidate / NOTEBOOK
    document = object_fields(json.loads(source.read_bytes()))
    rows = object_rows(document["cells"])
    final = next(cell for cell in reversed(rows) if cell["cell_type"] == "code")
    text = final["source"]
    assert isinstance(text, list)
    final["source"] = [
        *text,
        '\n(root / "examples/research/comparison.ipynb").write_bytes(b"deliberately changed native source")\n',
    ]
    document["cells"] = rows
    source.write_text(json.dumps(document))
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(source)],
        cwd=notebook_candidate,
        capture_output=True,
        check=True,
        timeout=30,
    )
    result = run_notebooks(notebook_candidate, "execute")
    assert result.returncode != 0
    assert "notebook check changed original source" in result.stderr
    assert source.read_bytes() == b"deliberately changed native source"


@pytest.mark.parametrize("damage", ["missing", "symlink", "empty", "tool", "mode"])
def test_missing_notebook_source_tool_and_invalid_mode_refuse(
    notebook_candidate: Path, damage: str
) -> None:
    """Refuse real missing/link source, empty Git discovery, absent interpreter and invalid mode.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Independent complete candidate; accepted source and tools stay untouched.
    damage : str
        Actual public discovery, interpreter or command refusal boundary.
    """
    source = notebook_candidate / NOTEBOOK
    python = sys.executable
    mode = "static"
    if damage in {"missing", "symlink", "empty"}:
        source.unlink()
        if damage == "symlink":
            source.symlink_to(ROOT / NOTEBOOK)
        elif damage == "empty":
            subprocess.run(
                [required_tool("git"), "rm", "--cached", "--", str(NOTEBOOK)],
                cwd=notebook_candidate,
                check=True,
                capture_output=True,
            )
    elif damage == "tool":
        python = str(notebook_candidate / "unavailable-python")
    else:
        mode = "unsupported"
    result = run_notebooks(notebook_candidate, mode, python=python)
    assert result.returncode != 0
    assert {
        "missing": "ENOENT",
        "symlink": "symlink",
        "empty": "no notebook source",
        "tool": "ENOENT",
        "mode": "usage:",
    }[damage] in result.stderr
