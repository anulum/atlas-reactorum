# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native Python/Node selected current and original profile parity.

"""Compare actual selected public APIs, source metadata and normal/optimized CLIs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from metadata.evidence_profiles.review_contract import ReviewError
from metadata.evidence_profiles.reviewed_entry import export_reviewed_profile, read_reviewed_profile

from .test_author_review_contract import PROFILE, REVIEW, ROOT, SNAPSHOT, read
from .test_reviewed_profile_products import PRODUCT
from .test_reviewed_profile_products import candidate as candidate
from .test_reviewed_profile_products import emitted as emitted
from .test_reviewed_profile_products import genuine_products as genuine_products

SCRIPT = ROOT / "metadata/evidence_profiles/reviewed_entry.py"
NODE_EXPORT = r"""
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const source=process.argv[1];
require(path.join(path.dirname(source),'presentation-text.js'));
const view=require(source);
const document=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const originalBytes=fs.readFileSync(process.argv[3]);
const original=JSON.parse(originalBytes.toString('utf8'));
const inputs={...original.inputs,
  original_profiles_sha256:crypto.createHash('sha256').update(originalBytes).digest('hex'),
  author_reviews_sha256:crypto.createHash('sha256').update(fs.readFileSync(process.argv[4])).digest('hex')};
process.stdout.write(view.exportProfile(document,inputs,original,process.argv[5]));
"""


@pytest.mark.parametrize(
    "entry_id",
    ["pwr", "phwr-candu", "molten-carbonate-fuel-cell", "muon-catalysed-fusion", "last"],
)
def test_real_selected_python_node_parity_and_independent_contexts(
    emitted: Path, entry_id: str
) -> None:
    """Compare genuine versioned selected output and preserve all three original contexts.

    Parameters
    ----------
    emitted : pathlib.Path
        Actual native-produced complete original/current source root.
    entry_id : str
        First, revised, additional-source, laboratory or final actual catalogue identity.
    """
    document = read(emitted / PRODUCT)
    if entry_id == "last":
        entry_id = cast(str, cast(list[dict[str, object]], document["records"])[-1]["id"])
    before = json.dumps(document)
    selected = read_reviewed_profile(emitted, SNAPSHOT, emitted / REVIEW, entry_id, document)
    exported = export_reviewed_profile(emitted, SNAPSHOT, emitted / REVIEW, entry_id, document)
    review = read(emitted / REVIEW)
    assert exported["schema_version"] == "atlas-entry-reviewed-profile-2.1.0"
    assert exported["author_review_context"] == {
        "author": review["author"],
        "reviewed_on": review["reviewed_on"],
    }
    assessment = cast(dict[str, object], exported["author_review"])
    assert assessment["complete_entry_review"] is True
    assert assessment["review_scope"] == "all-original-fields-and-selected-sources"
    assert assessment["review_basis"] == "author-source-inspection"
    assert assessment["independent_review"] is None
    for name in ["taxonomy_record", "original_profile", "author_review"]:
        assert exported[name] == selected[name]
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [
            node,
            "-e",
            NODE_EXPORT,
            str(ROOT / "04_interactive_presentation/taxonomy-reviewed-presentation.js"),
            str(emitted / PRODUCT),
            str(emitted / PROFILE),
            str(emitted / REVIEW),
            entry_id,
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == exported
    cast(dict[str, object], selected["taxonomy_record"])["name"] = "Caller mutation"
    cast(dict[str, object], exported["author_review"])["entity_category"] = "Caller mutation"
    cast(list[dict[str, object]], exported["sources"])[0]["title"] = "Caller mutation"
    assert json.dumps(document) == before


@pytest.mark.parametrize("identity", ["absent-entry", "invalid identity", 7])
def test_selected_actual_identity_refusal(emitted: Path, identity: object) -> None:
    """Refuse absent and malformed selectors through the complete real source admission.

    Parameters
    ----------
    emitted : pathlib.Path
        Genuine full source root whose late records remain present.
    identity : object
        Actual absent stable identity or malformed runtime selector.
    """
    for function in [read_reviewed_profile, export_reviewed_profile]:
        with pytest.raises(ReviewError):
            function(emitted, SNAPSHOT, emitted / REVIEW, cast(str, identity))


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("explicit", [False, True])
def test_actual_selected_cli_normal_optimized_and_explicit_input(
    emitted: Path, optimized: bool, explicit: bool
) -> None:
    """Export identical selected contexts through every actual CLI input path.

    Parameters
    ----------
    emitted : pathlib.Path
        Complete actual source and generated reviewed product.
    optimized : bool
        Whether the actual interpreter enables optimization.
    explicit : bool
        Whether the actual product path is explicitly selected.
    """
    args = [
        sys.executable,
        *(["-O"] if optimized else []),
        str(SCRIPT),
        "--root",
        str(emitted),
        "--snapshot",
        SNAPSHOT,
        "--reviews",
        str(emitted / REVIEW),
        "--entry",
        "phwr-candu",
    ]
    if explicit:
        args.extend(["--input", str(emitted / PRODUCT)])
    result = subprocess.run(args, capture_output=True, text=True, timeout=65)
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout) == export_reviewed_profile(
        emitted, SNAPSHOT, emitted / REVIEW, "phwr-candu"
    )


def test_actual_selected_cli_refuses_damaged_last_record_without_partial_output(
    emitted: Path,
) -> None:
    """Reject complete source corruption before emitting an otherwise valid early selection.

    Parameters
    ----------
    emitted : pathlib.Path
        Actual whole product with only its final current row deliberately changed.
    """
    document = read(emitted / PRODUCT)
    cast(list[dict[str, object]], document["records"])[-1]["name"] = "Unassessed final caption"
    (emitted / PRODUCT).write_text(json.dumps(document))
    for function in [read_reviewed_profile, export_reviewed_profile]:
        with pytest.raises(ReviewError, match="current rows differ"):
            function(emitted, SNAPSHOT, emitted / REVIEW, "pwr")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(emitted),
            "--snapshot",
            SNAPSHOT,
            "--reviews",
            str(emitted / REVIEW),
            "--entry",
            "pwr",
        ],
        capture_output=True,
        text=True,
        timeout=65,
    )
    assert result.returncode == 1 and not result.stdout
    assert result.stderr.startswith("reviewed entry: ")
    assert "Traceback" not in result.stderr and str(emitted) not in result.stderr
