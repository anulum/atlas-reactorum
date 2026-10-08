# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — public native web gates in actual owned Git candidates.
"""Exercise complete real web source and locked tools through the public CLI and Make."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate, run_node_fault
from .test_javascript_tools import required_tool

ROOT = Path(__file__).resolve().parents[1]
HTML = Path("04_interactive_presentation/index.html")
CSS = Path("04_interactive_presentation/styles.css")


@pytest.fixture
def web_candidate(tmp_path: Path) -> Path:
    """Create a real independent candidate with complete original source and installed tools.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owning temporary parent selected on the working disk.

    Returns
    -------
    pathlib.Path
        Separate candidate/index; dependency contents are read through native hard links.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    names = [
        "tools/web.cjs",
        "tools/css.cjs",
        "tools/source-files.cjs",
        "tools/htmlvalidate.cjs",
        "prettier.config.cjs",
        ".prettierignore",
        ".gitignore",
        "Makefile",
        str(HTML),
        str(CSS),
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    shutil.copytree(
        ROOT / "node_modules", root / "node_modules", copy_function=os.link, symlinks=True
    )
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", *names], cwd=root, check=True, capture_output=True
    )
    return root


def run_web(root: Path, mode: str, *, make: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the real complete public gate with a finite process deadline.

    Parameters
    ----------
    root : pathlib.Path
        Actual candidate working directory and index.
    mode : str
        HTML, CSS, format or explicit invalid mode.
    make : bool
        Whether to exercise the ordinary public Make entry point.

    Returns
    -------
    subprocess.CompletedProcess of str
        Original native process status and diagnostics.
    """
    command = [required_tool("node"), "tools/web.cjs", mode]
    if make:
        target = "native-web-format" if mode == "format" else "native-" + mode
        command = [required_tool("make"), target]
    return run_gate(
        root,
        command,
        ["tools/web.cjs", "tools/css.cjs", "tools/source-files.cjs"],
        dict(os.environ),
        150,
    )


@pytest.mark.parametrize("mode", ["html", "css", "format"])
@pytest.mark.parametrize("make", [False, True])
def test_actual_complete_source_qualifies(web_candidate: Path, mode: str, make: bool) -> None:
    """Require both public entry points to accept complete maintained source.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Independent current source and installed native graph.
    mode : str
        HTML, CSS or formatting contract selected for this case.
    make : bool
        Whether the owning command runs through the ordinary Make target.
    """
    result = run_web(web_candidate, mode, make=make)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("mode", "source", "mutation", "diagnostic"),
    [
        ("html", HTML, "<button>Missing type</button>", "no-implicit-button-type"),
        ("html", HTML, '<div aria-label="Wrong role"></div>', "aria-label-misuse"),
        ("html", HTML, "<section><button", "parser-error"),
        ("css", CSS, ".future{color:invalid-atlas-color}", "Mismatch"),
        ("css", CSS, ".future{unknown-atlas-property:red}", "Unknown property"),
        ("css", CSS, ".future{color:var(--absent)}", "no declaration or fallback"),
        ("css", CSS, ".future{???}", "is expected"),
        ("format", CSS, ".future{color:red}", "future"),
    ],
)
def test_new_root_source_enters_the_actual_gate(
    web_candidate: Path, mode: str, source: Path, mutation: str, diagnostic: str
) -> None:
    """Reject changed complete source under a new untracked root through native tools.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Independent complete current web candidate.
    mode : str
        Owning native source gate.
    source : pathlib.Path
        Original complete source whose bytes prefix the new candidate.
    mutation : str
        Real malformed or missing-contract source suffix.
    diagnostic : str
        Native observation proving the source was checked and refused.
    """
    target = web_candidate / "future" / source.name
    target.parent.mkdir()
    target.write_bytes((ROOT / source).read_bytes() + mutation.encode())
    result = run_web(web_candidate, mode, make=True)
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr


@pytest.mark.parametrize("kind", ["missing", "symlink", "empty-discovery"])
def test_unavailable_source_refuses(web_candidate: Path, kind: str) -> None:
    """Refuse missing/link source and an actually empty Git discovery result.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Owned source/index, leaving accepted source untouched.
    kind : str
        Native missing-file, link or index/source removal boundary.
    """
    source = web_candidate / HTML
    source.unlink()
    if kind == "symlink":
        source.symlink_to(ROOT / HTML)
    elif kind == "empty-discovery":
        subprocess.run(
            [required_tool("git"), "rm", "--cached", "--", str(HTML)],
            cwd=web_candidate,
            check=True,
            capture_output=True,
        )
    result = run_web(web_candidate, "html")
    assert result.returncode != 0
    assert {"missing": "ENOENT", "symlink": "symlink", "empty-discovery": "no native web source"}[
        kind
    ] in result.stderr


@pytest.mark.parametrize(
    "mode,package", [("html", "html-validate"), ("css", "css-tree"), ("format", "prettier")]
)
def test_wrong_native_version_refuses(web_candidate: Path, mode: str, package: str) -> None:
    """Break the candidate metadata hard link and refuse its changed native version.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Native installed graph copied into an independent candidate.
    mode : str
        Public check selecting that real tool.
    package : str
        Installed native tool whose own copied metadata is deliberately changed.
    """
    path = web_candidate / "node_modules" / package / "package.json"
    metadata = json.loads(path.read_text())
    path.unlink()
    metadata["version"] = "0.0.0"
    path.write_text(json.dumps(metadata))
    result = run_web(web_candidate, mode)
    assert result.returncode != 0
    assert "version mismatch" in result.stderr


def test_absent_native_graph_and_invalid_mode_refuse(web_candidate: Path) -> None:
    """Refuse unsupported commands and missing real tools without downloading replacements.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Owned complete source whose copied graph alone is removed.
    """
    invalid = run_web(web_candidate, "unsupported")
    assert invalid.returncode != 0 and "usage:" in invalid.stderr
    shutil.rmtree(web_candidate / "node_modules")
    missing = run_web(web_candidate, "html")
    assert missing.returncode != 0 and "Cannot find module" in missing.stderr


@pytest.mark.parametrize("fault", ["missing-runtime", "terminated-child"])
def test_native_web_child_process_failure_refuses(web_candidate: Path, fault: str) -> None:
    """Refuse native launch and signal failure without replacing the installed web formatter.

    Parameters
    ----------
    web_candidate : pathlib.Path
        Actual complete source/configuration and native package graph in an owned candidate.
    fault : str
        Loss of the copied native runtime path or termination of its actual child.
    """
    result = run_node_fault(
        web_candidate,
        "tools/web.cjs",
        ["tools/web.cjs", "tools/css.cjs", "tools/source-files.cjs"],
        dict(os.environ),
        fault,
    )
    assert result.returncode != 0
    assert ("ENOENT" if fault == "missing-runtime" else "no terminal status") in result.stderr
