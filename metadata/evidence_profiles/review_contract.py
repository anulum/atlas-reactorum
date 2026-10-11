# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — source-bound whole-catalogue author assessment admission.

"""Admit dated source assessments without rewriting original records or claims."""

from __future__ import annotations

import argparse
import calendar
import json
import math
import re
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker, SchemaError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class ReviewError(ValueError):
    """Refuse a stale, incomplete or source-inconsistent author assessment."""


def _mapping(value: object) -> dict[str, object]:
    """Retain unknown values after the owning schema has checked object shape."""
    return cast(dict[str, object], value)


def _records(value: object) -> list[dict[str, object]]:
    """Read record members only after baseline or assessment schema admission."""
    return cast(list[dict[str, object]], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse duplicate keys while retaining every original decoded member."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError("Author review contains duplicate JSON members.")
        result[key] = value
    return result


def _constant(value: str) -> object:
    """Reject the JSON decoder's nonfinite extension tokens."""
    raise ReviewError("Author review contains a nonfinite JSON number.")


def _float(value: str) -> float:
    """Reject finite-looking decimal tokens that overflow the native float."""
    result = float(value)
    if not math.isfinite(result):
        raise ReviewError("Author review contains a nonfinite JSON number.")
    return result


def read_review_json(path: Path) -> dict[str, object]:
    """Decode a complete review-related JSON object before semantic admission.

    Parameters
    ----------
    path : pathlib.Path
        Actual schema, author input or reviewed product to decode.

    Returns
    -------
    dict of str to object
        Complete decoded object, without duplicate or nonfinite members.

    Raises
    ------
    ReviewError
        The input is unreadable, malformed, nonobject or has invalid JSON numbers.
    """
    try:
        value: object = json.loads(
            path.read_text(encoding="utf8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
            parse_float=_float,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ReviewError("Author review input cannot be read as strict JSON.") from error
    if not isinstance(value, dict):
        raise ReviewError("Author review input must be an object.")
    return _mapping(value)


def _date_bounds(value: object) -> tuple[date, date] | None:
    """Bound partial dates without assigning unknown months or days."""
    item = _mapping(value)
    raw = item["value"]
    if raw is None:
        return None
    text = cast(str, raw)
    try:
        if item["precision"] == "day":
            day = date.fromisoformat(text)
            return day, day
        if item["precision"] == "month":
            year, month = map(int, text.split("-"))
            return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        year = int(text)
        return date(year, 1, 1), date(year, 12, 31)
    except ValueError as error:
        raise ReviewError("Author review has an invalid calendar date.") from error


def _additional_sources(
    document: dict[str, object], baseline: dict[str, object]
) -> dict[str, dict[str, object]]:
    """Admit separately identified source captures without altering the baseline."""
    sources: dict[str, dict[str, object]] = {}
    reviewed = cast(str, document["reviewed_on"])
    for source in [*_records(baseline["sources"]), *_records(document["additional_sources"])]:
        identity = cast(str, source["id"])
        if identity in sources:
            raise ReviewError("Author review duplicates a source identity.")
        captured = source["captured_at"]
        if source["capture_method"] == "retained-source-review":
            if captured is not None:
                raise ReviewError("Retained source acquisition remains unknown.")
        elif not isinstance(captured, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", captured
        ):
            raise ReviewError("Additional source acquisition must be a recorded UTC time.")
        if isinstance(captured, str) and captured[:10] > reviewed:
            raise ReviewError("Author review predates source acquisition.")
        if (source["format"] == "pdf" and cast(int, source["page_count"]) < 1) or (
            source["format"] != "pdf" and source["page_count"] != 0
        ):
            raise ReviewError("Additional source page count differs from its format.")
        sources[identity] = source
    return sources


def _observations(
    observations: list[dict[str, object]],
    sources: dict[str, dict[str, object]],
    reviewed_on: str,
    identities: set[str],
    used: set[str],
) -> None:
    """Bind each observation to its original source, locator and temporal role."""
    reviewed = date.fromisoformat(reviewed_on)
    for item in observations:
        identity = cast(str, item["id"])
        if identity in identities:
            raise ReviewError("Author review duplicates an observation identity.")
        identities.add(identity)
        source_id = cast(str, item["source_id"])
        if source_id not in sources:
            raise ReviewError("Author observation refers to an unknown source.")
        source = sources[source_id]
        pages = cast(list[int], item["pdf_pages"])
        printed = cast(list[str], item["printed_pages"])
        if source["format"] == "pdf":
            if (
                not pages
                or len(pages) != len(printed)
                or any(page > cast(int, source["page_count"]) for page in pages)
            ):
                raise ReviewError("Author observation has an invalid PDF locator.")
        elif pages or printed:
            raise ReviewError("Author observation has pages for a non-PDF source.")
        event = _date_bounds(item["event_date"])
        published = _date_bounds(item["published_date"])
        role = item["temporal_role"]
        if role == "attained" and event is not None and event[0] > reviewed:
            raise ReviewError("A future event cannot establish attained maturity.")
        if (
            role == "attained"
            and event is not None
            and published is not None
            and event[0] > published[1]
        ):
            raise ReviewError("An attained event postdates its reported publication.")
        if published is not None and published[0] > reviewed:
            raise ReviewError("A source publication postdates its assessment.")
        captured = source["captured_at"]
        if (
            published is not None
            and isinstance(captured, str)
            and published[0] > date.fromisoformat(captured[:10])
        ):
            raise ReviewError("A source publication postdates its acquisition.")
        used.add(source_id)


def _revisions(record: dict[str, object], fields: dict[str, object]) -> None:
    """Bind each explicit change to an admitted field correction, preserving history."""
    seen: set[str] = set()
    for item in _records(record["revisions"]):
        name = cast(str, item["field"])
        if name in seen:
            raise ReviewError("Author revision duplicates a field.")
        seen.add(name)
        if item["value"] == _mapping(fields[name])["original_value"]:
            raise ReviewError("Author revision must change its original value.")
    if any(
        (_mapping(field)["disposition"] == "correction-required") != (name in seen)
        for name, field in fields.items()
    ):
        raise ReviewError("Author revision differs from its field correction disposition.")


def validate_author_reviews(
    root: Path, snapshot_sha256: str, document: dict[str, object] | None = None
) -> dict[str, object]:
    """Validate all entry fields, original bindings and source-specific observations.

    Parameters
    ----------
    root : pathlib.Path
        Complete candidate containing the original source-bound profile inputs.
    snapshot_sha256 : str
        Explicit expected taxonomy hash; latest is never selected implicitly.
    document : dict of str to object or None
        Whole assessment input; None reads author_reviews.json from the candidate.

    Returns
    -------
    dict of str to object
        The admitted complete input without rewritten values or new acceptance flags.

    Raises
    ------
    ReviewError
        Baseline validation, input shape, original values, claims, dates or locators fail.
    """
    from metadata.evidence_profiles.review_dimensions import DimensionError, validate_dimensions
    from metadata.evidence_profiles.validate import ProfileError, validate_profiles

    try:
        baseline = validate_profiles(root, snapshot_sha256)
    except ProfileError as error:
        raise ReviewError("Original evidence profile cannot be validated.") from error
    if document is None:
        document = read_review_json(root / "metadata/evidence_profiles/author_reviews.json")
    schema = read_review_json(Path(__file__).with_name("author_review.schema.json"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise ReviewError("Author review schema is unavailable.") from error
    if next(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document), None
    ):
        raise ReviewError("Author review schema validation failed.")
    if document["baseline_inputs"] != baseline["inputs"]:
        raise ReviewError("Author review baseline hashes differ.")
    records = _records(document["records"])
    originals = _records(baseline["records"])
    reviewed_on = cast(str, document["reviewed_on"])
    if any(
        cast(str, _mapping(claim["citation"])["reviewed_on"]) > reviewed_on
        for original in originals
        for claim in _records(original["claims"])
    ):
        raise ReviewError("Author review predates the original source inspection.")
    if [item["entry_id"] for item in records] != [item["entry_id"] for item in originals]:
        raise ReviewError("Author review must cover the complete catalogue in order.")
    sources = _additional_sources(document, baseline)
    used: set[str] = set()
    observation_ids: set[str] = set()
    editorial = {
        "id",
        "domain",
        "family",
        "parent",
        "parent_id",
        "source_ids",
        "source_urls",
        "reviewed_on",
        "source_audit",
    }
    for record, original in zip(records, originals, strict=True):
        fields = _mapping(record["fields"])
        row = _mapping(original["taxonomy_record"])
        claims = {
            cast(str, claim["claim_id"]): _mapping(claim["citation"])
            for claim in _records(original["claims"])
        }
        if set(fields) != set(row):
            raise ReviewError("Author review omits an original taxonomy field.")
        for name, value in fields.items():
            field = _mapping(value)
            if field["original_value"] != row[name]:
                raise ReviewError("Author review changed an original taxonomy value.")
            claim_ids = cast(list[str], field["claim_ids"])
            source_ids = cast(list[str], field["source_ids"])
            if not set(claim_ids).issubset(claims) or not set(source_ids).issubset(sources):
                raise ReviewError("Author field assessment has an unknown claim or source.")
            if any(claims[identity]["source_id"] not in source_ids for identity in claim_ids):
                raise ReviewError("Author field omits a cited claim's source.")
            disposition = field["disposition"]
            if disposition in {"source-qualified", "correction-required"} and not source_ids:
                raise ReviewError("Source-qualified assessment has no supporting source.")
            if disposition == "context-only" and name not in {"temp", "mode"}:
                raise ReviewError("A scientific assertion cannot become descriptive context only.")
            if disposition == "editorial" and name not in editorial:
                raise ReviewError("A scientific field cannot become an editorial-only decision.")
            if disposition == "unscored" and (
                name not in {"scale", "control"} or row[name] is not None
            ):
                raise ReviewError("An unscored assessment must preserve an absent score.")
            used.update(source_ids)
        _revisions(record, fields)
        _observations(
            _records(record["observations"]),
            sources,
            cast(str, document["reviewed_on"]),
            observation_ids,
            used,
        )
        try:
            validate_dimensions(record, set(claims))
        except DimensionError as error:
            raise ReviewError(str(error)) from error
    if any(source["id"] not in used for source in _records(document["additional_sources"])):
        raise ReviewError("Author review includes an unused additional source.")
    try:
        if validate_profiles(root, snapshot_sha256) != baseline:
            raise ReviewError("Original evidence profile changed during assessment admission.")
    except ProfileError as error:
        raise ReviewError(
            "Original evidence profile changed during assessment admission."
        ) from error
    return document


def project_author_taxonomy(
    root: Path, snapshot_sha256: str, document: dict[str, object] | None = None
) -> list[dict[str, object]]:
    """Project explicitly revised rows after complete original and author admission.

    Parameters
    ----------
    root : pathlib.Path
        Complete candidate containing the original source-bound profile inputs.
    snapshot_sha256 : str
        Trusted original taxonomy hash; current is never selected implicitly.
    document : dict of str to object or None
        Complete author input; None reads the maintained default input path.

    Returns
    -------
    list of dict
        Complete ordered 21-field rows with independent copies of mutable values.
        Only explicitly supported revisions differ from the original context.

    Raises
    ------
    ReviewError
        Any original or author admission fails, including the last entry.
    """
    admitted = validate_author_reviews(root, snapshot_sha256, document)
    result: list[dict[str, object]] = []
    for record in _records(admitted["records"]):
        fields = _mapping(record["fields"])
        row = {name: deepcopy(_mapping(value)["original_value"]) for name, value in fields.items()}
        for revision in _records(record["revisions"]):
            row[cast(str, revision["field"])] = revision["value"]
        result.append(row)
    return result


def main(argv: list[str] | None = None) -> int:
    """Admit a complete author review through the same public validation API.

    Parameters
    ----------
    argv : list of str or None
        Public CLI arguments; None reads this process's argument vector.

    Returns
    -------
    int
        Zero with the complete input, one with a fixed caller-safe refusal.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--project", action="store_true")
    args = parser.parse_args(argv)
    try:
        document = read_review_json(args.reviews) if args.reviews is not None else None
        admitted: object = (
            project_author_taxonomy(args.root, args.snapshot, document)
            if args.project
            else validate_author_reviews(args.root, args.snapshot, document)
        )
    except ReviewError as error:
        print("author reviews: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(admitted, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
