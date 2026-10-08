# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native JavaScript tooling CLI regressions.

"""Exercise actual source discovery and locked native tools in owned Git candidates.

Candidates copy the public runner/configuration and the unchanged production
projection module. Native checks read an identical dependency graph linked into
each candidate. Corruption controls affect only owned source or fresh copies
of package metadata, never the accepted source or installed graph.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate, run_node_fault

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = Path("04_interactive_presentation/map/projection.js")


def required_tool(name: str) -> str:
    """Locate a native executable or fail without a replacement.

    Parameters
    ----------
    name : str
        Executable selected by the actual environment PATH.

    Returns
    -------
    str
        Actual executable path.

    Raises
    ------
    FileNotFoundError
        Required tool is unavailable.
    """
    tool = shutil.which(name)
    if tool is None:
        raise FileNotFoundError(name)
    return tool


@pytest.fixture
def javascript_candidate(tmp_path: Path) -> Path:
    """Create an owned Git candidate using actual public source and tooling.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-owned temporary parent on the selected working disk.

    Returns
    -------
    pathlib.Path
        Candidate with its own index and the actual native dependencies.

    Raises
    ------
    FileNotFoundError
        The public locked dependency graph has not been installed.
    """
    root = tmp_path / "candidate"
    root.mkdir()
    names = [
        "tools/javascript.cjs",
        "tests/native-gate-parent-coverage.cjs",
        "eslint.config.mjs",
        "prettier.config.cjs",
        "jsconfig.json",
        "package.json",
        ".prettierignore",
        ".gitignore",
        str(PROJECTION),
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    graph = ROOT / "node_modules"
    if not graph.is_dir():
        raise FileNotFoundError("run npm ci before native JavaScript regressions")
    shutil.copytree(graph, root / "node_modules", copy_function=os.link, symlinks=True)
    subprocess.run([required_tool("git"), "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(
        [required_tool("git"), "add", "--", *names],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


def run_tool(
    root: Path, mode: str, *, profile_parent: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the real public CLI and preserve native diagnostics.

    Parameters
    ----------
    root : pathlib.Path
        Owned candidate containing the real runner/configuration.
    mode : str
        Native check name or intentional invalid command.
    profile_parent : bool, optional
        Preserve precise coverage of the public gate while the complete source
        graph reaches an uninstrumented native compiler. Separate original
        native controls exercise and profile the same child configurations.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Unfiltered native status, stdout and stderr.
    """
    command = [required_tool("node"), "tools/javascript.cjs", mode]
    if profile_parent:
        command[1:1] = ["--require", "./tests/native-gate-parent-coverage.cjs"]
    return run_gate(
        root,
        command,
        [
            "tools/javascript.cjs",
            "tests/native-gate-parent-coverage.cjs",
            "eslint.config.mjs",
            "prettier.config.cjs",
        ],
        dict(os.environ),
        120,
    )


@pytest.mark.parametrize("mode", ("lint", "types", "format"))
def test_real_projection_and_runner_pass(javascript_candidate: Path, mode: str) -> None:
    """The actual projection module and public runner pass each owning native check."""
    result = run_tool(javascript_candidate, mode)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("mode", "suffix", "mutation", "diagnostic"),
    [
        ("lint", ".js", "\nundefinedAtlasSymbol();\n", "no-undef"),
        ("lint", ".cjs", "\nundefinedAtlasSymbol();\n", "no-undef"),
        ("lint", ".mjs", "\nundefinedAtlasSymbol();\n", "no-undef"),
        (
            "lint",
            ".js",
            "\nfunction undocumentedAtlasFunction(value) { return value; }\n",
            "jsdoc/require-jsdoc",
        ),
        ("types", ".js", "\n/** @type {number} */ const wrongAtlasType = 'text';\n", "TS2322"),
        ("format", ".js", "\nconst atlasSpacing={x:1};\n", "future"),
    ],
)
def test_new_root_source_enters_native_gate(
    javascript_candidate: Path, mode: str, suffix: str, mutation: str, diagnostic: str
) -> None:
    """New untracked source under a new root reaches the actual native checker.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Candidate with its own Git discovery and locked native graph.
    mode : str
        Lint, strict-type or format entry point.
    suffix : str
        New JS, CommonJS or module source extension.
    mutation : str
        Deliberate invalid suffix added to the unchanged production projection.
    diagnostic : str
        Native diagnostic proving the new file was checked.
    """
    source = javascript_candidate / "future" / ("projection" + suffix)
    source.parent.mkdir()
    source.write_bytes((ROOT / PROJECTION).read_bytes() + mutation.encode())
    result = run_tool(javascript_candidate, mode)
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr
    assert "future" in result.stdout + result.stderr


@pytest.mark.parametrize("kind", ("missing", "symlink"))
def test_tracked_source_refuses_before_tools(javascript_candidate: Path, kind: str) -> None:
    """Missing or symlinked tracked source cannot disappear from native discovery.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Owned candidate; the accepted projection remains untouched.
    kind : str
        Removal or replacement by a link to the unchanged production source.
    """
    source = javascript_candidate / PROJECTION
    source.unlink()
    if kind == "symlink":
        source.symlink_to(ROOT / PROJECTION)
    result = run_tool(javascript_candidate, "lint")
    assert result.returncode != 0
    assert "symlink" in result.stderr if kind == "symlink" else "ENOENT" in result.stderr


def test_missing_native_tool_refuses(javascript_candidate: Path) -> None:
    """An absent dependency graph fails without fetching a substitute checker."""
    shutil.rmtree(javascript_candidate / "node_modules")
    result = run_tool(javascript_candidate, "lint")
    assert result.returncode != 0
    assert "ENOENT" in result.stderr


def test_changed_native_tool_version_refuses(javascript_candidate: Path) -> None:
    """Altered owned package metadata cannot select an unqualified native version."""
    graph = javascript_candidate / "node_modules"
    shutil.rmtree(graph)
    graph.mkdir()
    tool = graph / "prettier"
    shutil.copytree(ROOT / "node_modules/prettier", tool)
    metadata_path = tool / "package.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["version"] = "0.0.0"
    metadata_path.write_text(json.dumps(metadata))
    result = run_tool(javascript_candidate, "format")
    assert result.returncode != 0
    assert "native tool version mismatch: prettier" in result.stderr


def test_unknown_command_refuses(javascript_candidate: Path) -> None:
    """An unknown mode cannot silently run an easier check or return success."""
    result = run_tool(javascript_candidate, "unknown")
    assert result.returncode != 0
    assert "usage:" in result.stderr


def test_new_handwritten_data_code_is_strictly_checked(javascript_candidate: Path) -> None:
    """A new data-directory script receives strict types rather than a directory waiver."""
    source = javascript_candidate / "04_interactive_presentation/data/new-model.js"
    source.parent.mkdir(parents=True)
    source.write_bytes(
        (ROOT / PROJECTION).read_bytes()
        + b"\n/** @type {number} */ const incorrectDataValue = 'text';\n"
    )
    result = run_tool(javascript_candidate, "types")
    assert result.returncode != 0
    assert "new-model.js" in result.stdout
    assert "TS2322" in result.stdout


@pytest.mark.parametrize("contents", ["null", '"invalid metadata"', "{}", '{"version":17}'])
def test_malformed_actual_package_metadata_refuses(
    javascript_candidate: Path, contents: str
) -> None:
    """Refuse malformed owned package metadata without substituting the real installed checker.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Original source/configuration and native graph; only its owned metadata link is replaced.
    contents : str
        Actual JSON container/property type corruption in the installed metadata copy.
    """
    path = javascript_candidate / "node_modules/prettier/package.json"
    path.unlink()
    path.write_text(contents)
    result = run_tool(javascript_candidate, "format")
    assert result.returncode != 0
    assert "native package metadata has no version" in result.stderr


def test_empty_actual_javascript_discovery_refuses(javascript_candidate: Path) -> None:
    """Refuse an actually empty tracked/new JavaScript source set before native checker selection.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Complete original tooling/source; only the isolated index/discovery configuration changes.
    """
    paths = [
        "tools/javascript.cjs",
        "tests/native-gate-parent-coverage.cjs",
        "eslint.config.mjs",
        "prettier.config.cjs",
        str(PROJECTION),
    ]
    subprocess.run(
        [required_tool("git"), "rm", "--cached", "--", *paths],
        cwd=javascript_candidate,
        check=True,
        capture_output=True,
    )
    with (javascript_candidate / ".git/info/exclude").open("a") as stream:
        stream.write("\n" + "\n".join(paths) + "\n")
    result = run_tool(javascript_candidate, "lint")
    assert result.returncode != 0
    assert "no native JavaScript source" in result.stderr


@pytest.mark.parametrize("fault", ["missing-runtime", "terminated-child"])
def test_native_child_process_failure_refuses(javascript_candidate: Path, fault: str) -> None:
    """Refuse actual launch and signal failures through the original public dispatcher and tool graph.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Actual unchanged projection/tool/configuration with an owned native binary copy.
    fault : str
        Real executable-path loss or termination of the actual child process.
    """
    result = run_node_fault(
        javascript_candidate,
        "tools/javascript.cjs",
        ["tools/javascript.cjs"],
        dict(os.environ),
        fault,
    )
    assert result.returncode != 0
    assert (
        "ENOENT" if fault == "missing-runtime" else "terminated without status"
    ) in result.stderr


@pytest.mark.parametrize(
    ("mode", "mutation", "diagnostic"),
    [
        ("lint", "\nundefinedAtlasSymbol();\n", "no-undef"),
        ("types", "\n/** @type {number} */ const wrongAtlasType = 'text';\n", "TS2322"),
        ("format", "\nconst atlasSpacing={x:1};\n", "future"),
    ],
)
def test_parent_scoped_profile_preserves_real_native_failures(
    javascript_candidate: Path, mode: str, mutation: str, diagnostic: str
) -> None:
    """Preserve actual checker failure for new source while profiling only its public gate parent.

    Parameters
    ----------
    javascript_candidate : pathlib.Path
        Complete owning source and locked native parser/compiler/formatter graph.
    mode : str
        Actual lint, strict-type or format entry point.
    mutation : str
        Native-invalid suffix added to the complete original projection.
    diagnostic : str
        Actual compiler diagnostic required from the genuine child process.
    """
    source = javascript_candidate / "future/projection.js"
    source.parent.mkdir()
    source.write_bytes((ROOT / PROJECTION).read_bytes() + mutation.encode())
    result = run_tool(javascript_candidate, mode, profile_parent=True)
    assert result.returncode != 0
    assert diagnostic in result.stdout + result.stderr
    assert "future" in result.stdout + result.stderr
