# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — blocking dependency audit command policy.

"""Pin complete native lock audits and their blocking correctness-CI dependency."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow_job(filename: str, name: str) -> dict[str, object]:
    """Read an actual workflow job with an explicitly validated object shape.

    Parameters
    ----------
    filename : str
        Public workflow path relative to the accepted repository.
    name : str
        Required job identifier.

    Returns
    -------
    dict[str, object]
        Actual job properties without fabricated defaults.

    Raises
    ------
    AssertionError
        The workflow, job map, requested job or its property names are malformed.
    """
    document: object = yaml.safe_load((ROOT / filename).read_text())
    assert isinstance(document, dict)
    jobs = document.get("jobs")
    assert isinstance(jobs, dict)
    job = jobs.get(name)
    assert isinstance(job, dict)
    result: dict[str, object] = {}
    for key, value in job.items():
        assert isinstance(key, str)
        result[key] = value
    return result


def run_steps(job: dict[str, object]) -> list[str]:
    """Read real shell steps while rejecting advisory failure handling.

    Parameters
    ----------
    job : dict[str, object]
        Actual audit or correctness-gate job.

    Returns
    -------
    list[str]
        Original shell commands in their authored order.

    Raises
    ------
    AssertionError
        A job or step permits failure, or the declared steps are malformed.
    """
    assert job.get("continue-on-error") in (None, False)
    steps = job.get("steps")
    assert isinstance(steps, list) and steps
    commands: list[str] = []
    for step in steps:
        assert isinstance(step, dict)
        assert step.get("continue-on-error") in (None, False)
        command = step.get("run")
        if command is not None:
            assert isinstance(command, str)
            commands.append(command)
    return commands


def test_make_audits_both_complete_locks_without_suppression() -> None:
    """The real Make recipe uses both full advisory audits with no weakened flags."""
    make = shutil.which("make")
    assert make is not None
    result = subprocess.run(
        [make, "--no-print-directory", "-n", "dependency-audit"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert result.stdout.splitlines() == [
        ".venv/bin/python -m pip_audit --require-hashes -r requirements-dev.txt",
        "npm audit --include=dev",
    ]


def test_correctness_gate_requires_the_blocking_audit_job() -> None:
    """Every correctness-CI run executes the audit recipe and requires its success."""
    audit = workflow_job(".github/workflows/ci.yml", "dependency-audit")
    commands = run_steps(audit)
    assert commands[-1] == "make dependency-audit"
    assert audit.get("if") is None
    gate = workflow_job(".github/workflows/ci.yml", "ci-gate")
    needs = gate.get("needs")
    assert isinstance(needs, list)
    assert "dependency-audit" in needs
    assert gate.get("if") == "${{ always() }}"
    assert 'job["result"] != "success"' in run_steps(gate)[-1]


def test_security_workflow_retains_both_unsuppressed_lock_audits() -> None:
    """The separate security workflow audits the same complete Python and npm locks."""
    commands = run_steps(workflow_job(".github/workflows/security-audit.yml", "audit"))
    assert "npm audit --include=dev" in commands
    assert ".venv/bin/python -m pip_audit --require-hashes -r requirements-dev.txt" in commands
