# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual registered shell and Python source hooks.
"""Exercise ordinary pre-commit source enrollment and native refusal in complete owned candidates."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

from ._native_gate_ranges import run_gate
from .test_notebook_tools import notebook_candidate as notebook_candidate


@pytest.mark.parametrize(
    ("hook", "relative"),
    [("native-shell", "tools/typecheck.sh"), ("native-python-types", "tools/research_objects.py")],
)
def test_registered_hook_checks_complete_new_root(
    notebook_candidate: Path, hook: str, relative: str
) -> None:
    """Accept complete original source in a new root, then reject its actual native defect.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Complete independent current source snapshot with its own index and hook configuration.
    hook : str
        Actual registered pre-commit identifier, without an alternate configuration.
    relative : str
        Complete original source copied into a new untracked directory with spaces.
    """
    root = notebook_candidate
    source = root / "future source" / Path(relative).name
    source.parent.mkdir()
    shutil.copy2(root / relative, source)
    original = source.read_bytes()
    command = [
        sys.executable,
        "-m",
        "pre_commit",
        "run",
        hook,
        "--files",
        str(source.relative_to(root)),
    ]
    modules = [".pre-commit-config.yaml", "Makefile", "tools/typecheck.sh"]
    accepted = run_gate(root, command, modules, dict(os.environ), 150)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert source.read_bytes() == original
    if hook == "native-shell":
        source.write_text(source.read_text().replace("    mypy_bin=", "   mypy_bin=", 1))
    else:
        source.write_bytes(original + b"\ndeliberate_type_failure: str = 7\n")
    refused = run_gate(root, command, modules, dict(os.environ), 150)
    assert refused.returncode != 0, refused.stdout + refused.stderr
    assert str(source.relative_to(root)) in refused.stdout + refused.stderr


@pytest.mark.parametrize("hook", ["native-shell", "native-python-types"])
def test_registered_hook_cannot_accept_missing_native_tool(
    notebook_candidate: Path, tmp_path: Path, hook: str
) -> None:
    """Reject a real missing formatter or explicitly unavailable strict compiler through pre-commit.

    Parameters
    ----------
    notebook_candidate : pathlib.Path
        Complete actual hook/source configuration and independent index.
    tmp_path : pathlib.Path
        Owning test directory for actual native executable links and absent tool path.
    hook : str
        Registered shell or Python source hook selected through the public CLI.
    """
    environment = dict(os.environ)
    if hook == "native-shell":
        tools = tmp_path / "actual-tools"
        tools.mkdir()
        for name in ("make", "git", "shellcheck", "grep", "mktemp", "rm", "xargs"):
            executable = shutil.which(name)
            assert executable is not None, name
            (tools / name).symlink_to(executable)
        environment["PATH"] = str(tools)
        source = "tools/typecheck.sh"
    else:
        environment["ATLAS_MYPY"] = str(tmp_path / "unavailable-mypy")
        source = "tools/research_objects.py"
    result = run_gate(
        notebook_candidate,
        [sys.executable, "-m", "pre_commit", "run", hook, "--files", source],
        [".pre-commit-config.yaml", "Makefile", "tools/typecheck.sh"],
        environment,
        150,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert hook in result.stdout
