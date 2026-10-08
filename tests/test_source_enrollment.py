# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native first-source language and declaration entry points.
"""Exercise actual declarations, source discovery and unsupported runtime/source refusal."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate
from .test_javascript_tools import ROOT, required_tool, run_tool
from .test_javascript_tools import javascript_candidate as javascript_candidate
from .test_notebook_tools import notebook_candidate as notebook_candidate


@pytest.fixture
def language_candidate(tmp_path: Path) -> Path:
    """Copy complete gate, projection and metadata inputs for the dependency-free language CLI.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owning directory for the independent source tree and native Git index.

    Returns
    -------
    pathlib.Path
        Actual complete source-discovery gate and unchanged production projection.
        Native compiler/formatter tests retain their separate installed package graph.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    names = [
        "tools/languages.cjs",
        "tools/source-files.cjs",
        "04_interactive_presentation/map/projection.js",
        ".gitignore",
        "package.json",
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    subprocess.run(
        [required_tool("git"), "init", "-q", str(root)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [required_tool("git"), "add", "--", *names],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return root


def run_languages(root: Path, node: str = "node") -> subprocess.CompletedProcess[str]:
    """Run the actual language gate with complete preserved source and native process evidence.

    Parameters
    ----------
    root : pathlib.Path
        Real source/index candidate and its actual newly introduced files.
    node : str
        Actual native executable name/path selected for the public command.

    Returns
    -------
    subprocess.CompletedProcess of str
        Original language-gate status and diagnostics, with durable source-bound V8 receipts.
    """
    modules = ["tools/languages.cjs", "tools/source-files.cjs"]
    for name in modules:
        shutil.copy2(ROOT / name, root / name)
    return run_gate(
        root, [required_tool(node), "tools/languages.cjs"], modules, dict(os.environ), 30
    )


def test_original_source_and_complete_declarations_enter_language_gate(
    language_candidate: Path,
) -> None:
    """Admit complete original implementation and declarations through actual first-source routing.

    Parameters
    ----------
    language_candidate : pathlib.Path
        Real original source/index with native installed tools.
    """
    future = language_candidate / "future"
    future.mkdir()
    shutil.copy2(ROOT / "04_interactive_presentation/browser-contracts.d.ts", future)
    result = run_languages(language_candidate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_complete_current_declarations_enter_each_native_gate(javascript_candidate: Path) -> None:
    """Check the actual complete browser declaration/source graph through each native entry point.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Owned source/index and actual locked native parser/compiler/formatter graph.
    """
    presentation = javascript_candidate / "04_interactive_presentation"
    shutil.copytree(ROOT / "04_interactive_presentation", presentation, dirs_exist_ok=True)
    for mode in ["lint", "types", "format"]:
        result = run_tool(javascript_candidate, mode, profile_parent=True)
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["lint", "types", "format"])
def test_new_declaration_root_cannot_escape_native_gate(
    javascript_candidate: Path, mode: str
) -> None:
    """Reject source-bound declaration mutations discovered under a new untracked root.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Actual source/configuration and native dependency graph.
    mode : str
        Declaration documentation, compiler or formatter boundary.
    """
    original = (ROOT / "04_interactive_presentation/browser-contracts.d.ts").read_text()
    source = javascript_candidate / "future" / "browser-contracts.d.ts"
    source.parent.mkdir()
    if mode == "lint":
        source.write_text(
            original + "\nexport interface UndocumentedNativeSource { value: number; }\n"
        )
        diagnostic = "jsdoc/require-jsdoc"
    elif mode == "types":
        source.write_text(
            original
            + "\n/** Invalid native declaration. */\nexport type BrokenNativeSource = UnregisteredAtlasType;\n"
        )
        diagnostic = "TS2304"
    else:
        source.write_text(original + "\nexport type AtlasNativeSpacing={value:number};\n")
        diagnostic = "future"
    result = run_tool(javascript_candidate, mode)
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr


@pytest.mark.parametrize("suffix", [".ts", ".rs", ".go", ".cpp", ".proto", ".node", ".wasm"])
def test_unqualified_source_or_backend_refuses_before_other_gates(
    language_candidate: Path, suffix: str
) -> None:
    """Refuse unqualified formats before running another language's unrelated checker.

    Parameters
    ----------
    language_candidate : pathlib.Path
        Independent actual Git candidate and installed native gate environment.
    suffix : str
        New maintained source/interface/backend format requiring its complete owning runtime.
    """
    source = language_candidate / "future" / ("projection" + suffix)
    source.parent.mkdir()
    source.write_bytes((ROOT / "04_interactive_presentation/map/projection.js").read_bytes())
    result = run_languages(language_candidate)
    assert result.returncode != 0
    assert "complete native language/backend qualification" in result.stderr
    assert str(source.relative_to(language_candidate)) in result.stderr


@pytest.mark.parametrize("suffix", [".php", ".dart", ".sql", ".purs", ".unregistered", ""])
def test_unknown_source_formats_require_explicit_owning_enrollment(
    language_candidate: Path, suffix: str
) -> None:
    """Refuse a complete original source under a format absent from the explicit native roles.

    Parameters
    ----------
    language_candidate : pathlib.Path
        Actual source/index candidate and original native gate dependencies.
    suffix : str
        Unregistered language, future format or extensionless source name.
    """
    source = language_candidate / "future" / ("projection" + suffix)
    source.parent.mkdir()
    source.write_bytes((ROOT / "04_interactive_presentation/map/projection.js").read_bytes())
    result = run_languages(language_candidate)
    assert result.returncode != 0
    assert "format requires explicit owning qualification" in result.stderr
    assert str(source.relative_to(language_candidate)) in result.stderr


def test_complete_current_source_and_asset_formats_have_explicit_roles(
    notebook_candidate: Path,
) -> None:
    """Retain every real current source and asset path through the original public language gate.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Complete independent actual checkout copy with its own native source index.
    """
    result = run_languages(notebook_candidate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_mixed_case_source_cannot_disappear_from_owning_discovery(
    language_candidate: Path,
) -> None:
    """Refuse actual source hidden from native case-sensitive pathspecs by a changed extension.

    Parameters
    ----------
    language_candidate : pathlib.Path
        Actual indexed source plus a new uppercase-suffix source candidate.
    """
    source = language_candidate / "future" / "projection.JS"
    source.parent.mkdir()
    source.write_bytes((ROOT / "04_interactive_presentation/map/projection.js").read_bytes())
    result = run_languages(language_candidate)
    assert result.returncode != 0
    assert "lowercase form" in result.stderr


@pytest.mark.parametrize(
    "statement", ['require("ffi-napi");', 'process.dlopen(module, "unqualified.node");']
)
def test_new_javascript_native_binding_requires_owning_qualification(
    javascript_candidate: Path, statement: str
) -> None:
    """Refuse direct unqualified native imports/loading through the ordinary native linter.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Actual original projection source, configuration and locked native graph.
    statement : str
        Deliberate new native loader/import on the complete maintained source.
    """
    source = javascript_candidate / "future" / "projection.cjs"
    source.parent.mkdir()
    source.write_bytes(
        (ROOT / "04_interactive_presentation/map/projection.js").read_bytes()
        + ("\n" + statement + "\n").encode()
    )
    result = run_tool(javascript_candidate, "lint")
    assert result.returncode != 0
    assert "no-restricted-" in result.stdout + result.stderr
