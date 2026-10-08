# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_make_native.py

"""Exercise the public native Make gates with real source and native tools.

Each disposable Git candidate retains the complete current shell and JavaScript
source set. New files, source mutations and tool selection are changed only in
that owned candidate; the accepted repository and its index remain intact.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHELL_SOURCE = Path("tools/typecheck.sh")
JS_SOURCE = Path("04_interactive_presentation/map/projection.js")


def required_tool(name: str) -> str:
    """Resolve an actual native executable without an ambient shell lookup.

    Parameters
    ----------
    name
        Required installed tool name from the current test environment.

    Returns
    -------
    str
        Executable path resolved by the actual PATH selection.

    Raises
    ------
    FileNotFoundError
        The required tool is unavailable; the check cannot become a pass.
    """
    executable = shutil.which(name)
    if executable is None:
        raise FileNotFoundError(name)
    return executable


@pytest.fixture
def native_candidate(tmp_path: Path) -> Path:
    """Copy the complete native source cohort into a disposable Git repository.

    Parameters
    ----------
    tmp_path
        Pytest-owned temporary parent; source bytes are copied without edits.

    Returns
    -------
    pathlib.Path
        Candidate root with its own index, Makefile, ignore and editor rules.
        No command in this fixture stages or changes the accepted repository.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    paths = subprocess.check_output(
        [
            required_tool("git"),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--deduplicate",
            "-z",
            "--",
            "*.sh",
            "*.js",
            "*.cjs",
            "*.mjs",
        ],
        cwd=ROOT,
    ).split(b"\0")
    names = ["Makefile", ".gitignore", ".editorconfig"]
    names.extend(os.fsdecode(path) for path in paths if path)
    for name in names:
        source = ROOT / name
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", *names], cwd=root, check=True, capture_output=True
    )
    return root


def run_gate(root: Path, target: str) -> subprocess.CompletedProcess[str]:
    """Run the actual Make target and retain its native status and diagnostics.

    Parameters
    ----------
    root
        Disposable candidate containing the original public Makefile.
    target
        One native shell or JavaScript quality target.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Real exit status and decoded stdout/stderr; findings are not substituted.
    """
    return subprocess.run(
        [required_tool("make"), target], cwd=root, text=True, capture_output=True, timeout=120
    )


@pytest.mark.parametrize("target", ["native-shell", "native-javascript"])
def test_complete_native_source_passes(native_candidate: Path, target: str) -> None:
    """The unmodified complete source cohort passes its owning native Make gate."""
    result = run_gate(native_candidate, target)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("suffix", "target", "source"),
    [
        (".sh", "native-shell", SHELL_SOURCE),
        (".js", "native-javascript", JS_SOURCE),
        (".cjs", "native-javascript", JS_SOURCE),
        (".mjs", "native-javascript", JS_SOURCE),
    ],
)
def test_new_source_enrols_without_allowlist(
    native_candidate: Path, suffix: str, target: str, source: Path
) -> None:
    """A new untracked source with spaces passes, then a real syntax defect fails.

    The copied existing source enters a new directory without a Makefile or
    index update. Removing its final closing delimiter must become a native
    finding; filename splitting or a fixed allowlist would incorrectly pass.
    """
    new_source = native_candidate / "00 new domain" / f"new source{suffix}"
    new_source.parent.mkdir()
    original = (native_candidate / source).read_text()
    new_source.write_text(original)
    accepted = run_gate(native_candidate, target)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    delimiter = "}" if suffix != ".sh" else '"'
    position = original.rfind(delimiter)
    assert position >= 0
    new_source.write_text(original[:position] + original[position + 1 :])
    refused = run_gate(native_candidate, target)
    assert refused.returncode != 0
    assert new_source.name in refused.stdout + refused.stderr


@pytest.mark.parametrize(
    ("target", "source"),
    [("native-shell", SHELL_SOURCE), ("native-javascript", JS_SOURCE)],
)
def test_missing_tracked_source_refuses(native_candidate: Path, target: str, source: Path) -> None:
    """A still-indexed source cannot disappear silently from a native gate."""
    (native_candidate / source).unlink()
    result = run_gate(native_candidate, target)
    assert result.returncode != 0
    assert str(source) in result.stderr


@pytest.mark.parametrize(
    ("target", "source"),
    [("native-shell", SHELL_SOURCE), ("native-javascript", JS_SOURCE)],
)
def test_symlink_source_refuses(
    native_candidate: Path, tmp_path: Path, target: str, source: Path
) -> None:
    """A source symlink to a readable valid external copy refuses before linting."""
    original = native_candidate / source
    external = tmp_path / original.name
    shutil.copy2(original, external)
    original.unlink()
    original.symlink_to(external)
    result = run_gate(native_candidate, target)
    assert result.returncode != 0
    assert "symlink" in result.stderr
    assert external.read_bytes() == (ROOT / source).read_bytes()


@pytest.mark.parametrize(
    ("target", "missing_tool"),
    [
        ("native-shell", "shellcheck"),
        ("native-shell", "shfmt"),
        ("native-javascript", "node"),
        ("native-javascript", "git"),
    ],
)
def test_missing_native_tool_refuses(
    native_candidate: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    missing_tool: str,
) -> None:
    """A PATH of actual native tools with one required tool absent cannot pass."""
    tool_path = tmp_path / "native-tools"
    tool_path.mkdir()
    for name in ("make", "git", "shellcheck", "shfmt", "node", "grep", "mktemp", "rm", "xargs"):
        if name == missing_tool:
            continue
        executable = shutil.which(name)
        assert executable is not None, f"Required test tool unavailable: {name}"
        (tool_path / name).symlink_to(executable)
    monkeypatch.setenv("PATH", str(tool_path))
    result = run_gate(native_candidate, target)
    assert result.returncode != 0


def test_shell_format_finding_propagates(native_candidate: Path) -> None:
    """ShellCheck acceptance cannot hide an actual shfmt formatting finding."""
    source = native_candidate / SHELL_SOURCE
    original = source.read_text()
    assert "    mypy_bin=" in original
    source.write_text(original.replace("    mypy_bin=", "   mypy_bin=", 1))
    lint = subprocess.run(
        [required_tool("shellcheck"), "--severity=style", str(source)],
        text=True,
        capture_output=True,
    )
    assert lint.returncode == 0, lint.stderr
    result = run_gate(native_candidate, "native-shell")
    assert result.returncode != 0
    assert str(SHELL_SOURCE) in result.stdout
