# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power-unit documentary admission
"""Admit power-unit source metadata without confusing captures with permission."""

from __future__ import annotations

import datetime as dt
import re
from typing import cast
from urllib.parse import urlparse

FIELDS = frozenset({"operator", "reactor_type"})
OPERATOR_ROLES = frozenset(
    {
        "actual_operator",
        "historical_operator",
        "explicit_intended_operator",
        "explicit_designated_future_operator",
        "licensed_project_organisation_combined_install_and_operate",
    }
)
DESIGN_ROLES = frozenset({"historical_design", "proposed_design"})
NATIVE_CLASSES = frozenset(
    {
        "native_original_pdf",
        "native_original_html",
        "native_original_facsimile",
        "native_original_spreadsheet",
    }
)
CONTEXT_FIELDS = (
    "unit_name",
    "plant_name",
    "country",
    "status",
    "lat",
    "lon",
    "model",
    "owner",
    "nameplate_mw",
    "operator",
    "reactor_type",
)


def mapping(value: object) -> dict[str, object]:
    """Require a JSON object with textual keys, preserving its original values."""
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("power admission requires an object with string keys")
    return cast(dict[str, object], value)


def sequence(value: object) -> list[object]:
    """Require a JSON array without coercing scalars or implicit absence."""
    if not isinstance(value, list):
        raise ValueError("power admission requires an array")
    return cast(list[object], value)


def text(row: dict[str, object], field: str, *, empty: bool = False) -> str:
    """Require a textual cell; only explicitly permitted cells may be empty."""
    value = row.get(field)
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"power admission requires text: {field}")
    return value


def digest(value: object) -> str:
    """Admit a lowercase SHA-256 binding rather than a caller's arbitrary label."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("power admission requires a SHA-256 binding")
    return value


def https_url(value: object) -> str:
    """Require an HTTPS source locator without embedded credentials."""
    if not isinstance(value, str):
        raise ValueError("power source URL must be text")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("power source URL must be credential-free HTTPS")
    return value


def integer(value: object, minimum: int, maximum: int) -> bool:
    """Check a bounded mathematical JSON integer, excluding booleans and fractions."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and minimum <= value <= maximum
        and value == int(value)
    )


def document_date(row: dict[str, object]) -> None:
    """Validate documentary precision and basis independently of capture time.

    Unknown publication dates remain empty. A report year or page modification
    date is permitted only with its own explicit basis; neither is an event date.
    """
    value = text(row, "document_date", empty=True)
    precision = text(row, "date_precision")
    text(row, "date_basis")
    if precision == "unknown":
        if value:
            raise ValueError("unknown power document date must be empty")
        return
    if precision == "month_range":
        if re.fullmatch(r"\d{4}-\d{2}/\d{4}-\d{2}", value) is None:
            raise ValueError("power documentary month range is malformed")
        try:
            start, end = (dt.date.fromisoformat(part + "-01") for part in value.split("/"))
        except ValueError as error:
            raise ValueError("power documentary month range is invalid") from error
        if start > end:
            raise ValueError("power documentary month range is reversed")
        return
    formats = {"year": r"\d{4}", "month": r"\d{4}-\d{2}", "day": r"\d{4}-\d{2}-\d{2}"}
    if precision not in formats or re.fullmatch(formats[precision], value) is None:
        raise ValueError("power document date differs from its precision")
    try:
        dt.date.fromisoformat(value + {"year": "-01-01", "month": "-01", "day": ""}[precision])
    except ValueError as error:
        raise ValueError("power document date is invalid") from error


def admit_sources(value: object) -> dict[str, dict[str, object]]:
    """Admit source custody records; documentary eligibility remains explicit.

    Parameters
    ----------
    value : object
        Source array from the complete producer bundle. Refused requests and
        non-documents may remain as attempts but cannot support selected values.

    Returns
    -------
    dict
        Original records indexed by unique source identity.

    Raises
    ------
    ValueError
        A source identity, URL, capture, digest or eligibility proof is invalid.
    """
    sources: dict[str, dict[str, object]] = {}
    for item in sequence(value):
        row = mapping(item)
        identity = text(row, "source_id")
        if identity in sources:
            raise ValueError("duplicate power source identity")
        https_url(row.get("url"))
        https_url(row.get("requested_url"))
        captured = text(row, "captured_at")
        if (
            re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
                r"(?:\.[0-9]{1,6})?(?:Z|\+00:00)",
                captured,
            )
            is None
        ):
            raise ValueError("power capture timestamp must use canonical UTC ISO format")
        try:
            dt.datetime.fromisoformat(captured)
        except ValueError as error:
            raise ValueError("power capture timestamp is invalid") from error
        if type(row.get("eligible_for_selection")) is not bool:
            raise ValueError("power source eligibility must be explicit")
        if type(row.get("body_complete")) is not bool:
            raise ValueError("power source body completeness must be explicit")
        status = row.get("http_status")
        size = row.get("body_bytes")
        if "http_status" not in row or (status is not None and not integer(status, 100, 599)):
            raise ValueError("power source HTTP status is invalid")
        if "body_bytes" not in row or (size is not None and not integer(size, 0, 9007199254740991)):
            raise ValueError("power source body byte count is invalid")
        body_sha256 = text(row, "body_sha256", empty=True)
        if body_sha256:
            digest(body_sha256)
        state = text(row, "body_state")
        if state not in {"qualified_document", "context_only", "capture_attempt"}:
            raise ValueError("power source body state is invalid")
        native_class = text(row, "native_class", empty=True)
        if state != "capture_attempt":
            if (
                row["http_status"] != 200
                or row.get("body_complete") is not True
                or not integer(size, 1, 9007199254740991)
                or native_class not in NATIVE_CLASSES
            ):
                raise ValueError("power documentary context needs a complete native document")
            digest(row.get("body_sha256"))
        if row["eligible_for_selection"]:
            if state != "qualified_document":
                raise ValueError("selected power source needs documentary qualification")
        elif state == "qualified_document":
            raise ValueError("qualified power document cannot lack selection eligibility")
        text(row, "rights_scope")
        if row["rights_scope"] != "citation_and_factual_metadata_only":
            raise ValueError("power source rights must exclude original body redistribution")
        sources[identity] = row
    return sources


def admit_citations(
    value: object, sources: dict[str, dict[str, object]], *, selected: bool
) -> list[dict[str, object]]:
    """Bind factual citations to original documents; keep capture attempts separate.

    Parameters
    ----------
    value : object
        Array of source identities, exact locators and documentary date meanings.
    sources : dict
        Original custody registry admitted by ``admit_sources``.
    selected : bool
        Whether these citations support a selected scalar, requiring eligibility.

    Returns
    -------
    list of dict
        Original citations in their original order.

    Raises
    ------
    ValueError
        A citation is duplicate, missing, an attempt, or unqualified for selection.
    """
    citations: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in sequence(value):
        row = mapping(item)
        identity = text(row, "source_id")
        locator = text(row, "locator")
        source = sources.get(identity)
        if source is None or source["body_state"] == "capture_attempt":
            raise ValueError("power citation requires a retained documentary context")
        if selected and source["eligible_for_selection"] is not True:
            raise ValueError("power selected citation is not qualified")
        if (identity, locator) in seen:
            raise ValueError("duplicate power citation")
        seen.add((identity, locator))
        document_date(row)
        citations.append(row)
    if selected and not citations:
        raise ValueError("selected power value requires a source citation")
    return citations
