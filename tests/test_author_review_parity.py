# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_author_review_parity.py

"""Require Python and native JavaScript agreement on the actual whole author input."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

import pytest

from metadata.evidence_profiles.review_contract import ReviewError, validate_author_reviews

from .test_author_review_contract import PROFILE, REVIEW, ROOT, SNAPSHOT, read, records
from .test_author_review_contract import candidate as candidate

PROGRAM = """
const fs=require('node:fs');
const api=require(process.argv[1]);
const review=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const baseline=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
try {api.read(review,baseline); process.stdout.write('accepted');}
catch {process.stdout.write('refused');}
"""


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "original",
        "source",
        "claim",
        "unbound",
        "future",
        "publication",
        "capture",
        "score",
        "completion",
        "scope",
        "basis",
        "independent",
        "category",
    ],
)
def test_real_whole_input_agrees_across_python_and_node(candidate: Path, fault: str) -> None:
    """Compare actual native public APIs using the same complete source bytes.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine all135 source assessment and original baseline inputs.
    fault : str
        Concrete semantic corruption, or the unchanged full input for acceptance.
    """
    doc = read(candidate / REVIEW)
    first = records(doc)[0]
    fields = cast(dict[str, dict[str, object]], first["fields"])
    observation = cast(list[dict[str, object]], first["observations"])[0]
    if fault == "original":
        fields["principle"]["original_value"] = "changed original statement"
    elif fault == "source":
        fields["principle"]["source_ids"] = ["absent-source"]
    elif fault == "claim":
        fields["principle"]["claim_ids"] = ["absent:principle:1"]
    elif fault == "unbound":
        fields["principle"]["source_ids"] = []
        fields["principle"]["claim_ids"] = []
    elif fault == "future":
        observation["event_date"] = {"value": "2030-01-01", "precision": "day"}
    elif fault == "publication":
        observation["published_date"] = {"value": "2023", "precision": "year"}
    elif fault == "capture":
        cast(list[dict[str, object]], doc["additional_sources"])[0]["captured_at"] = (
            "2026-10-08T07:28:31+01:00"
        )
    elif fault == "score":
        fields["principle"]["disposition"] = "unscored"
    elif fault == "completion":
        first["complete_entry_review"] = False
    elif fault == "scope":
        first["review_scope"] = "all-hardware-qualified"
    elif fault == "basis":
        first["review_basis"] = "independent-review"
    elif fault == "independent":
        first["independent_review"] = {"accepted": True}
    elif fault == "category":
        first["entity_category"] = "unknown"
    accepted = True
    try:
        assert validate_author_reviews(candidate, SNAPSHOT, doc) == doc
    except ReviewError:
        accepted = False
    assert accepted is (fault == "none")
    original = (candidate / PROFILE).read_bytes()
    (candidate / REVIEW).write_text(json.dumps(doc))
    executable = shutil.which("node")
    assert executable is not None
    result = subprocess.run(
        [
            executable,
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
    assert result.returncode == 0, result.stderr
    assert result.stdout == ("accepted" if accepted else "refused")
    assert (candidate / PROFILE).read_bytes() == original
