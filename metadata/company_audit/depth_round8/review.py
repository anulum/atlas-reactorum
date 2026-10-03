#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round8/review.py
"""Check the full reviewed input packet and its deterministic historical selection.

These checks validate structure, identity and provenance. They do not establish
prototype isotope, independent replication, physical gap closure or release rights.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from metadata.company_audit.depth_round8.tables import (
    BINDING_FIELDS,
    EARLY_FIELDS,
    MATRIX_FIELDS,
    PROFILE_FIELDS,
    SOURCE_FIELDS,
    read_table,
)

HERE = Path(__file__).resolve().parent
DATE = "2026-09-30"
HISTORY = ("depth_round4", "depth_round5", "depth_round6", "depth_round7")
INPUT_NAMES = ("reviewed_profiles.tsv", "reviewed_sources.tsv", "field_source_bindings.tsv")

REVIEW_FIELDS = "organization source_record_id round4_gap_fields metadata_fields_reviewed review_scope remaining_verification audit_date".split()
ENRICHED_FIELDS = "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates"


@dataclass
class Reviewed:
    """Validated original profile text with its associated source context.

    Attributes
    ----------
    profiles, sources, bindings, gaps : list of dict
        Full profile, source, field-association and selected original matrix rows.
    inputs : tuple of pathlib.Path
        Actual source files protected against output replacement.
    """

    profiles: list[dict[str, str]]
    sources: list[dict[str, str]]
    bindings: list[dict[str, str]]
    gaps: list[dict[str, str]]
    inputs: tuple[Path, ...]


def select_gaps(matrix: Path, history: Path) -> tuple[list[dict[str, str]], tuple[Path, ...]]:
    """Rank the full previous matrix after excluding historical identities.

    Parameters
    ----------
    matrix : pathlib.Path
        Complete original company gap matrix.
    history : pathlib.Path
        Directory containing all four historical overlay layers.

    Returns
    -------
    tuple
        Ten ranked matrix rows and all protected historical inputs.

    Raises
    ------
    ValueError
        Identities, record IDs, ranking or the candidate set are invalid.
    """
    gaps = read_table(matrix, MATRIX_FIELDS)
    names = [row["organization"] for row in gaps]
    ids = [row["record_id"] for row in gaps]
    if (
        len(set(names)) != len(names)
        or len(set(ids)) != len(ids)
        or any(not x.strip() for x in [*names, *ids])
    ):
        raise ValueError("duplicate or blank matrix identity")
    for row in gaps:
        if int(row["priority_score"]) < 0 or int(row["source_row"]) < 1:
            raise ValueError("invalid matrix ranking")
    excluded: set[str] = set()
    paths = tuple(history / layer / "enrichment_overlays.tsv" for layer in HISTORY)
    for layer, path in zip(HISTORY, paths, strict=True):
        rows = read_table(path, EARLY_FIELDS if layer in HISTORY[:2] else PROFILE_FIELDS)
        previous = [row["organization"] for row in rows]
        if len(set(previous)) != len(previous) or any(not x.strip() for x in previous):
            raise ValueError("duplicate or blank historical identity")
        if set(previous) & excluded or not set(previous) <= set(names):
            raise ValueError("historical identity overlap or unknown target")
        for row in rows:
            if row["source_record_id"] != gaps[names.index(row["organization"])]["record_id"]:
                raise ValueError("historical record identity mismatch")
        excluded.update(previous)
    eligible = [
        row
        for row in gaps
        if row["organization"] not in excluded
        and {"fuel_cycle", "status"} & set(row["gap_fields"].split(";"))
    ]
    eligible.sort(key=lambda row: (-int(row["priority_score"]), int(row["source_row"])))
    if len(eligible) < 10:
        raise ValueError("fewer than ten eligible targets")
    return eligible[:10], (matrix, *paths)


def check_provenance(
    profiles: list[dict[str, str]], sources: list[dict[str, str]], bindings: list[dict[str, str]]
) -> None:
    """Require nonblank dated text and exact company/source/field associations.

    Parameters
    ----------
    profiles, sources, bindings : list of dict
        Complete reviewed tables, with their producer schemas already checked.

    Raises
    ------
    ValueError
        A date, URL, source association or substantive field binding is invalid.
    """
    for row in [*profiles, *sources, *bindings]:
        if any(not value.strip() for value in row.values()):
            raise ValueError("blank reviewed field")
    by_id = {row["source_id"]: row for row in sources}
    if len(by_id) != len(sources):
        raise ValueError("duplicate source ID")
    for source in sources:
        parsed = urlsplit(source["url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("invalid anonymous HTTPS source URL")
        if source["accessed_on"] != DATE:
            raise ValueError("source access date mismatch")
    used: set[str] = set()
    for row in profiles:
        if (
            row["match_rule"] != "exact normalized organization name"
            or row["audit_date"] != DATE
            or row["fields_enriched"] != ENRICHED_FIELDS
        ):
            raise ValueError("profile matching, date or enrichment contract mismatch")
        source_ids = row["source_ids"].split(";")
        expected = [
            source["source_id"]
            for source in sources
            if source["organization"] == row["organization"]
        ]
        if source_ids != expected:
            raise ValueError("profile/source ownership or order mismatch")
        links = [
            row["enriched_official_url"],
            *[url.strip() for url in row["enriched_independent_urls"].split(";")],
        ]
        for url in links:
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("invalid anonymous HTTPS profile URL")
        expected_links = list(dict.fromkeys(by_id[key]["url"] for key in source_ids[1:]))
        expected_dates = "; ".join(
            f"{key}: {by_id[key]['source_date']} (accessed {by_id[key]['accessed_on']})"
            for key in source_ids
        )
        if links[1:] != expected_links or row["source_dates"] != expected_dates:
            raise ValueError("source link/date binding mismatch")
        used.update(source_ids)
    if used != set(by_id):
        raise ValueError("unassociated source")
    expected_pairs = [
        (row["organization"], field) for row in profiles for field in PROFILE_FIELDS[4:10]
    ]
    if [(row["organization"], row["field"]) for row in bindings] != expected_pairs:
        raise ValueError("field association order/completeness mismatch")
    for binding in bindings:
        keys = binding["source_ids"].split(";")
        if len(set(keys)) != len(keys) or any(
            key not in by_id or by_id[key]["organization"] != binding["organization"]
            for key in keys
        ):
            raise ValueError("invalid field source ownership")
        if binding["reviewed_on"] != DATE:
            raise ValueError("field review date mismatch")


def load_review(directory: Path, matrix: Path, history: Path) -> Reviewed:
    """Load the whole reviewed packet and verify its original ranked identities.

    Parameters
    ----------
    directory : pathlib.Path
        Frozen reviewed-input directory.
    matrix, history : pathlib.Path
        Actual previous matrix and historical layers.

    Returns
    -------
    Reviewed
        Verbatim original paraphrases and source limitations, not evidence approval.

    Raises
    ------
    ValueError
        Selected profile identities or source associations do not agree.
    """
    paths = tuple(directory / name for name in INPUT_NAMES)
    profiles = read_table(paths[0], PROFILE_FIELDS)
    sources = read_table(paths[1], SOURCE_FIELDS)
    bindings = read_table(paths[2], BINDING_FIELDS)
    gaps, prior_inputs = select_gaps(matrix, history)
    if [row["organization"] for row in profiles] != [row["organization"] for row in gaps]:
        raise ValueError("profile selection/order differs from deterministic rule")
    if any(
        row["source_record_id"] != gap["record_id"] for row, gap in zip(profiles, gaps, strict=True)
    ):
        raise ValueError("selected record identity mismatch")
    check_provenance(profiles, sources, bindings)
    return Reviewed(profiles, sources, bindings, gaps, (*paths, *prior_inputs))


def gap_reviews(review: Reviewed) -> list[dict[str, str]]:
    """Document reviewed metadata without counting physical gaps as closed.

    Parameters
    ----------
    review : Reviewed
        Complete validated packet with the original selected gap rows.

    Returns
    -------
    list of dict
        Record-specific review accounting and explicit technical limitations.
    """
    return [
        dict(
            zip(
                REVIEW_FIELDS,
                [
                    row["organization"],
                    row["source_record_id"],
                    gap["gap_fields"],
                    str(len(gap["gap_fields"].split(";"))),
                    "dated metadata review; physical gap closure not established",
                    row["overlay_note"],
                    DATE,
                ],
                strict=True,
            )
        )
        for row, gap in zip(review.profiles, review.gaps, strict=True)
    ]


def main() -> None:
    """Inspect the complete source packet through its read-only CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-directory", type=Path, default=HERE / "reviewed_inputs")
    parser.add_argument(
        "--gap-matrix", type=Path, default=HERE.parent / "depth_round4/gap_matrix.tsv"
    )
    parser.add_argument("--history-directory", type=Path, default=HERE.parent)
    args = parser.parse_args()
    try:
        review = load_review(args.input_directory, args.gap_matrix, args.history_directory)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"REVIEW FAILED: {error}")
        raise SystemExit(1) from None
    print(
        json.dumps(
            {
                "audit_date": DATE,
                "profile_count": len(review.profiles),
                "source_count": len(review.sources),
                "metadata_gap_fields_reviewed": sum(
                    int(row["metadata_fields_reviewed"]) for row in gap_reviews(review)
                ),
                "physical_gap_closure": "not established by structural validation",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
