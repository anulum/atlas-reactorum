# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — historical acquisition refusal conformance

"""Exercise the real historical API and CLI without collecting publisher data."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT
from .conftest import load_module

SCRIPT = ROOT / "05_global_reactor_map/imports/fusion/build_dataset.py"
REFUSAL = "Historical FusionBenchmark live acquisition is not approved; use the pinned FFDB build."


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://127.0.0.1:9/source",
        "http://127.0.0.1:9/source",
        "file:///unapproved-source",
        "ftp://127.0.0.1/source",
        "data:application/json,{}",
        "custom:source",
        "https://person:password@127.0.0.1:9/source",
    ],
)
def test_every_historical_fetch_refuses_before_opening_a_protocol(url: str) -> None:
    """Require the exact historical-acquisition refusal for every supplied protocol and URL form."""
    module = load_module(
        "05_global_reactor_map/imports/fusion/build_dataset.py", "atlas_historical_acquisition"
    )
    with pytest.raises(module.HistoricalAcquisitionRefused, match="not approved") as error:
        module.fetch(url)
    assert str(error.value) == REFUSAL


def test_historical_main_refuses_and_preserves_every_retained_layer() -> None:
    """Refuse the historical main entry point while preserving every retained fusion TSV hash."""
    module = load_module(
        "05_global_reactor_map/imports/fusion/build_dataset.py", "atlas_historical_acquisition"
    )
    paths = sorted(SCRIPT.parent.rglob("*.tsv"))
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    with pytest.raises(module.HistoricalAcquisitionRefused, match="not approved"):
        module.main()
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


@pytest.mark.parametrize("optimize", [False, True])
def test_actual_historical_cli_refuses_with_authored_exit_and_no_output(
    tmp_path: Path, optimize: bool
) -> None:
    """Return the authored CLI refusal normally and under -O without output or source changes."""
    paths = sorted(SCRIPT.parent.rglob("*.tsv"))
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    command = [sys.executable, *(["-O"] if optimize else []), str(SCRIPT)]
    environment = dict(os.environ)
    environment.setdefault("COVERAGE_FILE", str(tmp_path.parent / "historical-cli.coverage"))
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == REFUSAL + "\n"
    assert not list(tmp_path.iterdir())
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
