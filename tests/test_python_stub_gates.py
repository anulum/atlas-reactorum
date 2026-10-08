# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — generated declaration/runtime and Python discovery conformance.
"""Bind real generated stubs to the complete original public research object implementation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate
from .test_javascript_tools import ROOT, required_tool


@pytest.fixture
def stub_candidate(tmp_path: Path) -> Path:
    """Generate a real interface from complete original source in an independent Git candidate.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Working-disk temporary parent owned by this public gate case.

    Returns
    -------
    pathlib.Path
        Original runtime source, native generated stub and actual public gate/configuration.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    names = [
        "tools/stubs.cjs",
        "tools/source-files.cjs",
        "tools/typecheck.sh",
        "pyproject.toml",
        ".gitignore",
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    source = root / "research_objects.py"
    source.write_bytes((ROOT / "tools/research_objects.py").read_bytes())
    declaration = generate_stub(source, tmp_path / "generated")
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", *names, source.name, declaration.name],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


def generate_stub(source: Path, generated: Path) -> Path:
    """Generate an actual native interface for a complete original or deliberately changed source.

    Parameters
    ----------
    source : pathlib.Path
        Complete implementation whose actual public signatures and native header are retained.
    generated : pathlib.Path
        Owner-selected independent output directory for the real stubgen invocation.

    Returns
    -------
    pathlib.Path
        Native generated declaration beside its actual source counterpart.
    """
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from mypy.stubgen import main; main()",
            "--no-import",
            "--parse-only",
            "--include-private",
            "-o",
            str(generated),
            str(source),
        ],
        cwd=source.parent,
        check=True,
        capture_output=True,
        timeout=30,
    )
    declaration = generated / source.with_suffix(".pyi").name
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(declaration)],
        cwd=source.parent,
        check=True,
        capture_output=True,
        timeout=30,
    )
    lines = source.read_text().splitlines()
    if lines[0].startswith("#!"):
        lines = lines[1:]
    header = "\n".join(lines[:7]) + "\n"
    target = source.with_suffix(".pyi")
    target.write_text(header + declaration.read_text())
    return target


def run_stub(
    root: Path, *, types: bool = False, optimized: bool = False, python: str | None = sys.executable
) -> subprocess.CompletedProcess[str]:
    """Invoke the actual declaration/runtime gate or complete Python source/stub discovery.

    Parameters
    ----------
    root : pathlib.Path
        Complete original candidate and actual native interface.
    types : bool
        Whether to use the public shell/MyPy entry point.
    optimized : bool
        Whether actual interpreter optimization is enabled for the native subprocesses.
    python : str or None
        Actual interpreter, unavailable executable or None for the project default.

    Returns
    -------
    subprocess.CompletedProcess of str
        Original native status and diagnostics within a finite deadline.
    """
    command = [required_tool("node"), "tools/stubs.cjs"]
    if types:
        command = [required_tool("bash"), "tools/typecheck.sh"]
    environment = {
        **os.environ,
        "ATLAS_MYPY": str(Path(sys.executable).parent / "mypy"),
    }
    if optimized:
        environment["PYTHONOPTIMIZE"] = "1"
    if python is None:
        environment.pop("ATLAS_PYTHON", None)
    else:
        environment["ATLAS_PYTHON"] = python
    return run_gate(
        root,
        command,
        ["tools/stubs.cjs", "tools/source-files.cjs"],
        environment,
        120,
    )


@pytest.mark.parametrize("types", [False, True])
def test_original_generated_interface_and_actual_runtime_qualify(
    stub_candidate: Path, types: bool
) -> None:
    """Accept the actual public implementation and its unmodified native generated declaration.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Real source/generated declaration with independent index and original tools.
    types : bool
        Native interface/runtime or strict source-discovery entry point.
    """
    result = run_stub(stub_candidate, types=types)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("damage", ["return", "parameter", "missing-symbol", "missing-source"])
def test_changed_stub_or_missing_runtime_refuses(stub_candidate: Path, damage: str) -> None:
    """Reject changed types/signatures, omitted public symbols and unavailable implementations.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Complete real declaration and runtime candidate.
    damage : str
        Actual declaration or source mutation; accepted inputs remain untouched.
    """
    stub = stub_candidate / "research_objects.pyi"
    text = stub.read_text()
    if damage == "return":
        stub.write_text(text.replace("dict[str, object]", "str", 1))
    elif damage == "parameter":
        stub.write_text(text.replace("value: object", "renamed: object", 1))
    elif damage == "missing-symbol":
        stub.write_text(
            "\n".join(line for line in text.splitlines() if not line.startswith("def object_rows"))
            + "\n"
        )
    else:
        source = stub_candidate / "research_objects.py"
        source.rename(source.with_suffix(".unavailable"))
    result = run_stub(stub_candidate)
    assert result.returncode != 0
    assert (
        "native source interface" in result.stderr
        if damage != "missing-source"
        else "ENOENT" in result.stderr
    )


def test_new_stub_root_and_missing_tracked_source_reach_real_discovery(
    stub_candidate: Path,
) -> None:
    """Refuse a native type error in a new stub-only root and missing indexed source.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Real source/declaration with actual native MyPy and source/index discovery.
    """
    future = stub_candidate / "future"
    future.mkdir()
    source = future / "unregistered.pyi"
    source.write_text("def unavailable(value: UnregisteredAtlasType) -> object: ...\n")
    result = run_stub(stub_candidate, types=True)
    assert result.returncode != 0
    assert "UnregisteredAtlasType" in result.stdout
    source.unlink()
    (stub_candidate / "research_objects.py").unlink()
    result = run_stub(stub_candidate, types=True)
    assert result.returncode != 0
    assert "source unavailable" in result.stderr


def test_native_version_mismatch_refuses_under_real_optimization(stub_candidate: Path) -> None:
    """Refuse changed native metadata even when the actual interpreter disables assertions.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Original generated declaration/runtime and the actual native metadata import parent.
    """
    native = distribution("mypy")
    files = native.files
    assert files is not None
    entry = next(file for file in files if file.name == "METADATA")
    source = Path(str(native.locate_file(entry.parent)))
    metadata = stub_candidate / source.name
    shutil.copytree(source, metadata)
    path = metadata / "METADATA"
    original = path.read_text()
    assert "Version: 2.3.1" in original
    path.write_text(original.replace("Version: 2.3.1", "Version: 0.0.0"))
    result = run_stub(stub_candidate, optimized=True)
    assert result.returncode != 0
    assert "native Python stub tool version mismatch" in result.stderr


@pytest.mark.parametrize("python", [None, "unavailable-python"])
def test_missing_native_interpreter_refuses(stub_candidate: Path, python: str | None) -> None:
    """Refuse actual unavailable explicit and project-default interpreter paths.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Complete original generated declaration and real implementation.
    python : str or None
        Unavailable executable name or absence of an explicit interpreter selection.
    """
    selected = str(stub_candidate / python) if python is not None else None
    result = run_stub(stub_candidate, python=selected)
    assert result.returncode != 0
    assert "ENOENT" in result.stderr


def test_new_orphan_stub_requires_its_actual_implementation(stub_candidate: Path) -> None:
    """Refuse a complete native declaration introduced without its runtime source in a new root.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Qualified original declaration used as exact source for the newly unpaired interface.
    """
    future = stub_candidate / "future"
    future.mkdir()
    shutil.copy2(stub_candidate / "research_objects.pyi", future / "research_objects.pyi")
    result = run_stub(stub_candidate)
    assert result.returncode != 0
    assert "needs its qualified source counterpart: future/research_objects.pyi" in result.stderr


def test_original_executable_source_interface_qualifies(
    stub_candidate: Path, tmp_path: Path
) -> None:
    """Bind the complete original executable rebuild module through native declaration and runtime checks.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Existing complete gate/native configuration and original qualified interface.
    tmp_path : pathlib.Path
        Owning output parent for the real native executable-module declaration.
    """
    source = stub_candidate / "atlas_rebuild.py"
    source.write_bytes((ROOT / "tools/rebuild.py").read_bytes())
    declaration = generate_stub(source, tmp_path / "executable-declaration")
    original = source.read_bytes(), declaration.read_bytes()
    result = run_stub(stub_candidate)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Native Python stub counterparts qualified: 2" in result.stdout
    assert original == (source.read_bytes(), declaration.read_bytes())


def test_real_runtime_import_cannot_change_qualified_source(stub_candidate: Path) -> None:
    """Detect actual input mutation during a native import after the original interface matches.

    Parameters
    ----------
    stub_candidate : pathlib.Path
        Complete original object-reader source and real generated declaration in an owned candidate.
    """
    source = stub_candidate / "research_objects.py"
    source.write_bytes(source.read_bytes() + b'\nopen(__file__, "ab").write(b"\\n")\n')
    before = source.read_bytes()
    result = run_stub(stub_candidate)
    assert result.returncode != 0
    assert "stub qualification changed input source" in result.stderr
    assert source.read_bytes() == before + b"\n"
