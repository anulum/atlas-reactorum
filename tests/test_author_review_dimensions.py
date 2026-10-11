# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — entry-owned classification and development evidence.

"""Exercise actual whole-input dimension admission and Python/JavaScript parity."""

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
from .test_author_review_parity import PROGRAM


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "no-evidence",
        "foreign-claim",
        "foreign-observation",
        "duplicate-facet",
        "missing-role",
        "unknown-axis",
        "no-stage-evidence",
        "claim-only-stage",
        "duplicate-stage",
        "forecast",
        "wrong-topic",
        "wrong-object",
        "industrial-experiment",
        "unknown-stage",
        "unknown-object",
        "unknown-observed-object",
    ],
)
def test_whole_source_dimensions_agree_across_native_readers(candidate: Path, fault: str) -> None:
    """Preserve scoped attained objects or reject the same mutated full source input.

    Parameters
    ----------
    candidate : pathlib.Path
        Genuine complete assessment and original source/profile inputs.
    fault : str
        Actual ownership, temporal or evidence-object corruption to introduce.
    """
    document = read(candidate / REVIEW)
    rows = records(document)
    first = rows[0]
    facet = cast(list[dict[str, object]], first["facets"])[0]
    stage = cast(list[dict[str, object]], first["development_assessments"])[0]
    observation = cast(list[dict[str, object]], first["observations"])[0]
    hydrogen = next(
        row for row in rows if row["entry_id"] == "nuclear-heat-coupled-to-hydrogen-production"
    )
    muon = next(row for row in rows if row["entry_id"] == "muon-catalysed-fusion")
    if fault == "no-evidence":
        facet["claim_ids"] = []
    elif fault == "foreign-claim":
        facet["claim_ids"] = ["integral-pwr:classification:1"]
    elif fault == "foreign-observation":
        facet["observation_ids"] = ["nine-mile-point-electrical-hydrogen-pilot"]
    elif fault == "duplicate-facet":
        cast(list[dict[str, object]], first["facets"]).append(facet.copy())
    elif fault == "missing-role":
        facet["value"] = "subtype"
    elif fault == "unknown-axis":
        facet["axis"] = "unknown"
    elif fault == "no-stage-evidence":
        stage["observation_ids"] = []
    elif fault == "claim-only-stage":
        stage["observation_ids"] = []
        stage["claim_ids"] = ["pwr:strength:1"]
    elif fault == "duplicate-stage":
        cast(list[dict[str, object]], first["development_assessments"]).append(stage.copy())
    elif fault == "forecast":
        cast(list[dict[str, object]], hydrogen["development_assessments"])[0]["observation_ids"] = [
            "httr-hydrogen-future-project-schedule"
        ]
    elif fault == "wrong-topic":
        observation["topic"] = "classification"
    elif fault == "wrong-object":
        stage["evidence_object"] = "experiment"
    elif fault == "industrial-experiment":
        cast(list[dict[str, object]], muon["development_assessments"])[0]["stage"] = "industrial"
    elif fault == "unknown-stage":
        stage["stage"] = "unknown"
    elif fault == "unknown-object":
        stage["evidence_object"] = "unknown"
    elif fault == "unknown-observed-object":
        observation["evidence_object"] = "unknown"
    accepted = True
    try:
        assert validate_author_reviews(candidate, SNAPSHOT, document) == document
    except ReviewError:
        accepted = False
    assert accepted is (fault == "none")
    if accepted:
        assert sum(len(cast(list[object], row["facets"])) for row in rows) == 138
        assert sum(len(cast(list[object], row["development_assessments"])) for row in rows) == 21
        assert sum(len(cast(list[object], row["observations"])) for row in rows) == 31
    original = (candidate / PROFILE).read_bytes()
    (candidate / REVIEW).write_text(json.dumps(document))
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
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
    assert result.returncode == 0, result.stderr
    assert result.stdout == ("accepted" if accepted else "refused")
    assert (candidate / PROFILE).read_bytes() == original
