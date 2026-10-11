# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — explicit correction and full taxonomy projection.

"""Exercise source-bound revisions through the actual Python/Node APIs and CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from metadata.evidence_profiles.review_contract import ReviewError, project_author_taxonomy

from .test_author_review_contract import PROFILE, REVIEW, ROOT, SCRIPT, SNAPSHOT, read, records
from .test_author_review_contract import candidate as candidate

PROGRAM = """
const fs=require('node:fs');const api=require(process.argv[1]);
const review=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const baseline=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
try {process.stdout.write(JSON.stringify(api.project(review,baseline)));}
catch {process.stdout.write('refused');}
"""


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "duplicate",
        "unchanged",
        "missing",
        "unassessed",
        "identity",
        "last-entry",
        "contextual-science",
    ],
)
def test_actual_whole_projection_and_refusals_match_node(candidate: Path, fault: str) -> None:
    """Project every actual row or reject the same source/correction fault in both languages.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine all135 input with unchanged original source/profile bindings.
    fault : str
        Explicit revision fault or unchanged source data for projection equality.
    """
    doc = read(candidate / REVIEW)
    row = next(item for item in records(doc) if item["entry_id"] == "phwr-candu")
    revisions = cast(list[dict[str, object]], row["revisions"])
    if fault == "duplicate":
        revisions.append(revisions[0].copy())
    elif fault == "unchanged":
        revisions[0]["value"] = cast(dict[str, dict[str, object]], row["fields"])["name"][
            "original_value"
        ]
    elif fault == "missing":
        row["revisions"] = []
    elif fault == "unassessed":
        records(doc)[0]["revisions"] = [{"field": "name", "value": "Unassessed PWR caption"}]
    elif fault == "identity":
        revisions[0]["field"] = "id"
    elif fault == "contextual-science":
        cast(dict[str, dict[str, object]], row["fields"])["principle"]["disposition"] = (
            "context-only"
        )
    elif fault == "last-entry":
        cast(dict[str, dict[str, object]], records(doc)[-1]["fields"])["principle"][
            "original_value"
        ] = "changed last original"
    result: list[dict[str, object]] | None = None
    try:
        result = project_author_taxonomy(candidate, SNAPSHOT, doc)
    except ReviewError:
        pass
    assert (result is not None) is (fault == "none")
    original_profile = (candidate / PROFILE).read_bytes()
    (candidate / REVIEW).write_text(json.dumps(doc))
    node = shutil.which("node")
    assert node is not None
    process = subprocess.run(
        [
            node,
            "-e",
            PROGRAM,
            str(ROOT / "04_interactive_presentation/taxonomy-author-review.js"),
            str(candidate / REVIEW),
            str(candidate / PROFILE),
        ],
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert process.returncode == 0, process.stderr
    if result is None:
        assert process.stdout == "refused"
    else:
        assert json.loads(process.stdout) == result
        assert (
            sum(
                cell["disposition"] == "context-only"
                for item in records(doc)
                for cell in cast(dict[str, dict[str, object]], item["fields"]).values()
            )
            == 270
        )
        originals = records(read(candidate / PROFILE))
        changed: list[tuple[object, str, object]] = []
        for projected, source in zip(result, originals, strict=True):
            context = cast(dict[str, object], source["taxonomy_record"])
            assert projected.keys() == context.keys()
            assert projected["id"] == context["id"]
            changed.extend(
                (projected["id"], key, value)
                for key, value in projected.items()
                if value != context[key]
            )
        assert changed == [
            ("integral-pwr", "maturity", "deployed"),
            ("phwr-candu", "name", "Pressure-tube PHWR including CANDU"),
            ("heavy-water-pressure-vessel-reactor", "maturity", "deployed"),
            ("magnox-gas-cooled-reactor", "maturity", "deployed"),
            ("prismatic-htgr", "maturity", "deployed"),
            ("lead-bismuth-fast-reactor", "maturity", "deployed"),
            (
                "nuclear-heat-coupled-to-hydrogen-production",
                "name",
                "Nuclear energy coupled to hydrogen production",
            ),
        ]
        before = json.dumps(doc)
        cast(list[str], result[0]["source_ids"]).append("caller-mutation")
        cast(list[str], result[0]["source_urls"]).reverse()
        assert json.dumps(doc) == before
    assert (candidate / PROFILE).read_bytes() == original_profile


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("explicit", [False, True])
def test_real_projection_cli_keeps_all135_original_ids(
    candidate: Path, optimized: bool, explicit: bool
) -> None:
    """Use the public projection switch under both interpreter modes/input paths.

    Parameters
    ----------
    candidate : pathlib.Path
        Complete genuine original and assessment inputs.
    optimized : bool
        Whether the actual interpreter uses optimization.
    explicit : bool
        Whether the assessment path is explicit or the owning default.
    """
    before = (candidate / REVIEW).read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimized else []),
            str(SCRIPT),
            "--root",
            str(candidate),
            "--snapshot",
            SNAPSHOT,
            "--project",
            *(["--reviews", str(candidate / REVIEW)] if explicit else []),
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == project_author_taxonomy(candidate, SNAPSHOT)
    assert (candidate / REVIEW).read_bytes() == before
