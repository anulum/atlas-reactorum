# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — selected current/original profile export without new acceptance.

"""Read and export a selected reviewed entry only after whole source admission."""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import cast

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from metadata.evidence_profiles.review_contract import ReviewError, read_review_json
from metadata.evidence_profiles.reviewed_profiles import validate_reviewed_profiles


def _selected(document: dict[str, object], entry_id: str) -> dict[str, object]:
    """Select independent contexts from a completely admitted ordered product."""
    if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry_id):
        raise ReviewError("Reviewed profile identity is invalid.")
    rows = cast(list[dict[str, object]], document["records"])
    index = next((index for index, row in enumerate(rows) if row["id"] == entry_id), None)
    if index is None:
        raise ReviewError("Reviewed profile selection is absent.")
    original = cast(dict[str, object], document["original_profiles"])
    author = cast(dict[str, object], document["author_reviews"])
    return deepcopy(
        {
            "taxonomy_record": rows[index],
            "original_profile": cast(list[dict[str, object]], original["records"])[index],
            "author_review": cast(list[dict[str, object]], author["records"])[index],
        }
    )


def read_reviewed_profile(
    root: Path,
    snapshot_sha256: str,
    reviews_path: Path,
    entry_id: str,
    document: dict[str, object] | None = None,
) -> dict[str, object]:
    """Read the selected current row, original profile and dated author assessment.

    Parameters
    ----------
    root : pathlib.Path
        Complete original source root with the reviewed product.
    snapshot_sha256 : str
        Explicit trusted original taxonomy hash.
    reviews_path : pathlib.Path
        Actual source-bound author input.
    entry_id : str
        Stable selected identity, checked after the entire catalogue is admitted.
    document : dict of str to object or None
        Explicit whole product; None reads the maintained product path.

    Returns
    -------
    dict of str to object
        Independent copies of all three selected contexts.

    Raises
    ------
    ReviewError
        Whole source admission or selected identity fails.
    """
    admitted = validate_reviewed_profiles(root, snapshot_sha256, reviews_path, document)
    return _selected(admitted, entry_id)


def export_reviewed_profile(
    root: Path,
    snapshot_sha256: str,
    reviews_path: Path,
    entry_id: str,
    document: dict[str, object] | None = None,
) -> dict[str, object]:
    """Export the selected contexts and all supporting source metadata.

    Parameters
    ----------
    root : pathlib.Path
        Complete actual original sources and generated reviewed product.
    snapshot_sha256 : str
        Explicit trusted original taxonomy hash.
    reviews_path : pathlib.Path
        Actual author input bound by the whole product.
    entry_id : str
        Stable selected identity, never an implicit latest selector.
    document : dict of str to object or None
        Explicit whole product; None reads the maintained JSON product.

    Returns
    -------
    dict of str to object
        Single-entry versioned current/original profile with source rights and hashes.

    Raises
    ------
    ReviewError
        Whole source admission or the selected identity fails.
    """
    admitted = validate_reviewed_profiles(root, snapshot_sha256, reviews_path, document)
    selected = _selected(admitted, entry_id)
    original = cast(dict[str, object], selected["original_profile"])
    author = cast(dict[str, object], selected["author_review"])
    used = {
        cast(str, cast(dict[str, object], claim["citation"])["source_id"])
        for claim in cast(list[dict[str, object]], original["claims"])
    }
    for field in cast(dict[str, dict[str, object]], author["fields"]).values():
        used.update(cast(list[str], field["source_ids"]))
    used.update(
        cast(str, observation["source_id"])
        for observation in cast(list[dict[str, object]], author["observations"])
    )
    baseline = cast(dict[str, object], admitted["original_profiles"])
    assessment = cast(dict[str, object], admitted["author_reviews"])
    sources = [
        *cast(list[dict[str, object]], baseline["sources"]),
        *cast(list[dict[str, object]], assessment["additional_sources"]),
    ]
    return deepcopy(
        {
            "schema_version": "atlas-entry-reviewed-profile-2.1.0",
            "metadata_license": admitted["metadata_license"],
            "source_rights": admitted["source_rights"],
            "inputs": admitted["inputs"],
            "selected_entry_id": entry_id,
            "author_review_context": {
                "author": assessment["author"],
                "reviewed_on": assessment["reviewed_on"],
            },
            **selected,
            "sources": [source for source in sources if source["id"] in used],
        }
    )


def main(argv: list[str] | None = None) -> int:
    """Export the explicitly selected entry using the same whole-admission API.

    Parameters
    ----------
    argv : list of str or None
        Explicit process arguments; None reads the actual process vector.

    Returns
    -------
    int
        Zero with a complete selected export or one with fixed refusal text.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args(argv)
    try:
        document = read_review_json(args.input) if args.input is not None else None
        exported = export_reviewed_profile(
            args.root, args.snapshot, args.reviews, args.entry, document
        )
    except ReviewError as error:
        print("reviewed entry: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(exported, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
