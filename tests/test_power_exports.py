# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual power download and native parity
"""Parse every actual power CSV cell and compare native projection to original TSV."""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
from pathlib import Path

from .test_power_bundle import BUNDLE, DIRECTORY, ROOT, SOURCE


def test_native_projection_and_every_csv_cell(tmp_path: Path) -> None:
    """Exercise actual Node APIs against all original rows and complete published power records."""
    node = shutil.which("node")
    assert node is not None
    original = BUNDLE.read_source(SOURCE)
    packet = tmp_path / "packet.json"
    packet.write_text(
        json.dumps(
            {
                "baseline": original,
                "fields": BUNDLE.read_document(DIRECTORY / "primary-fields.json")["fields"],
                "sources": BUNDLE.read_document(DIRECTORY / "primary-sources.json")["sources"],
            }
        )
    )
    javascript = """
const fs=require('node:fs');
const P=require('./04_interactive_presentation/power-field-contract.js');
require('./04_interactive_presentation/application-data.js');
const E=require('./04_interactive_presentation/facility-export.js');
const input=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
const projected=P.project(input.baseline,input.fields,input.sources);
const rows=AtlasApplicationData.facilities(JSON.parse(fs.readFileSync('./04_interactive_presentation/data/global_reactors.sample.json','utf8'))).filter(row=>row.dataset_source==='05_global_reactor_map/imports/power_units/power_reactor_units.tsv');
process.stdout.write(JSON.stringify({projected,rows,csv:E.serialize(rows,'csv'),json:E.serialize(rows,'json')}));
"""
    result = subprocess.run(
        [node, "-e", javascript, str(packet)],
        cwd=ROOT,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    projection = BUNDLE.load_projection(SOURCE, DIRECTORY)
    assert projection is not None
    assert output["projected"] == {
        "rows": list(projection.rows),
        "decisions": list(projection.decisions),
        "source_records": list(projection.sources),
    }
    rows = output["rows"]
    assert len(rows) == 1823 and json.loads(output["json"]) == rows
    parsed = list(csv.DictReader(io.StringIO(output["csv"])))
    nested = {
        "field_observations",
        "power_field_decisions",
        "research_field_origins",
        "research_primary_assertions",
        "source_urls",
    }
    assert len(parsed) == len(rows)
    for record, cells in zip(rows, parsed, strict=True):
        for field, value in cells.items():
            if field in nested:
                assert json.loads(value) == record.get(field, [])
            else:
                expected = record.get(field)
                assert value == ("" if expected is None else str(expected))


def test_actual_power_cli_process() -> None:
    """Invoke the maintained script as the same actual offline release command."""
    result = subprocess.run(
        [
            os.environ.get("ATLAS_PYTHON", str(ROOT / ".venv/bin/python")),
            str(DIRECTORY / "build_power_projection.py"),
            str(SOURCE),
            str(DIRECTORY),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "1823 rows, 930 decisions, 54 qualified fields" in result.stdout
