# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — live publisher sources stay outside the correctness gate

"""Bind the separation of the correctness gate from live third-party sources.

A publisher that changes a page must produce a report, not a red gate. These
cases read the actual Make recipes and workflows that keep it so.
"""

from __future__ import annotations

import shutil
import subprocess

import yaml

from ._catalogue_inputs import ROOT
from .test_dependency_audit_policy import run_steps, workflow_job

CACHE_PREFIX = "industrial7-custody-"


def _dry_run(target: str, *variables: str) -> str:
    """Return the commands Make would run for a target, without running them."""
    make = shutil.which("make")
    assert make is not None
    result = subprocess.run(
        [make, "--no-print-directory", "-n", target, "VENV=.venv", *variables],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout


def test_gate_recipe_leaves_live_publisher_cases_out() -> None:
    """The blocking test recipe deselects live cases and the drift recipe selects only them."""
    assert '-m "not live_source"' in _dry_run("test")
    drift = _dry_run("source-drift", "CUSTODY=/absent/custody").splitlines()
    assert drift[-2].endswith("-m pytest tests/ -m live_source --no-cov")
    assert drift[-1].endswith('acquisition.py --directory "/absent/custody"')


def test_gate_reads_retained_sources_before_the_tests() -> None:
    """The gate restores the last validated sources and uses them only when one was found."""
    job = workflow_job(".github/workflows/ci.yml", "tests")
    steps = job["steps"]
    assert isinstance(steps, list)
    restore = next(step for step in steps if step.get("id") == "custody")
    assert str(restore["uses"]).startswith("actions/cache/restore@")
    assert restore["with"]["restore-keys"] == CACHE_PREFIX
    use = steps[steps.index(restore) + 1]
    assert use["if"] == "${{ steps.custody.outputs.cache-matched-key != '' }}"
    assert "ATLAS_INDUSTRIAL7_CAPTURE_DIR=" in use["run"]
    assert run_steps(job)[-1] == "make test"


def test_drift_report_runs_on_a_schedule_outside_the_gate() -> None:
    """The live acquisition is scheduled, cannot be skipped over, and no gate job needs it."""
    document = yaml.safe_load((ROOT / ".github/workflows/source-drift.yml").read_text())
    triggers = document[True]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    job = workflow_job(".github/workflows/source-drift.yml", "industrial-round-seven")
    commands = run_steps(job)
    assert any("make source-drift CUSTODY=" in command for command in commands)
    steps = job["steps"]
    assert isinstance(steps, list)
    assert str(steps[-1]["uses"]).startswith("actions/cache/save@")
    assert str(steps[-1]["with"]["key"]).startswith(CACHE_PREFIX)
    gate = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert "source-drift" not in str(gate["jobs"]["ci-gate"])


def test_changed_source_is_a_warning_and_never_replaces_the_retained_set() -> None:
    """A drifted source ends the run green with a warning; only a validated set is saved."""
    job = workflow_job(".github/workflows/source-drift.yml", "industrial-round-seven")
    steps = job["steps"]
    assert isinstance(steps, list)
    acquire = next(step for step in steps if step.get("id") == "acquire")
    script = str(acquire["run"])
    failure_branch = script.split("then", 1)[1].split("fi", 1)[0]
    assert "::warning title=Publisher source drift::" in failure_branch
    assert 'echo "validated=false" >>"$GITHUB_OUTPUT"' in failure_branch
    assert "exit 0" in failure_branch and "exit 1" not in script
    assert script.rstrip().endswith('echo "validated=true" >>"$GITHUB_OUTPUT"')
    assert steps[-1]["if"] == "steps.acquire.outputs.validated == 'true'"
