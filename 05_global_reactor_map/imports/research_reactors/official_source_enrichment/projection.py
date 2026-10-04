# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — primary research field projection
"""Project a complete reviewed field ledger without rewriting original source cells."""

from __future__ import annotations

import csv
import datetime
import io
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ("operator", "purpose", "first_criticality")
COLUMNS = (
    "stable_id",
    "field",
    "value",
    "selection",
    "source_id",
    "source_title",
    "source_url",
    "source_sha256",
    "source_class",
    "source_document_date",
    "source_capture_date",
    "locator",
    "scope",
    "rights",
    "date_precision",
    "assertion_basis",
    "related_evidence",
)
DECISIONS = frozenset(
    {
        "selected",
        "held",
        "unknown",
        "not_applicable",
        "never_critical",
        "planned",
        "composite",
        "unreviewed",
    }
)
NATIVE = frozenset({"native_original_pdf", "native_original_html", "native_original_facsimile"})


@dataclass(frozen=True)
class FieldProjection:
    """Complete original rows, selected fills and every reviewed disposition.

    Attributes
    ----------
    rows : dict of str to dict of str to str
        Copies of all baseline cells, with selected originally blank cells filled.
    assertions : tuple of dict of str to str
        Exact ledger cells, including held claims and explicit no-fill decisions.
    """

    rows: dict[str, dict[str, str]]
    assertions: tuple[dict[str, str], ...]


def _date(value: str) -> None:
    """Validate the actual calendar at the supplied year, month or day precision."""
    if not value:
        return
    if not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", value):
        raise ValueError("research date precision is invalid")
    padded = value + {4: "-01-01", 7: "-01", 10: ""}[len(value)]
    datetime.date.fromisoformat(padded)


def _url(value: str) -> None:
    """Refuse credentials, parser-normalised malformed links and non-HTTPS sources."""
    if not re.fullmatch(r"https://[^\s\\]+", value):
        raise ValueError("anonymous HTTPS source required")
    parsed = urlsplit(value)
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("anonymous HTTPS source required")
    # Accessing port also rejects malformed ports which urlsplit otherwise retains.
    if parsed.port is not None and not 0 < parsed.port <= 65535:
        raise ValueError("anonymous HTTPS source required")


def _related(value: str) -> None:
    """Validate retained corroborating or conflicting citations without discarding their wording."""
    if not value:
        return
    evidence: object = json.loads(value)
    allowed = {"source_id", "original_url", "sha256", "locator", "admissibility", "reported_value"}
    required = {"source_id", "original_url", "sha256"}
    if not isinstance(evidence, list):
        raise ValueError("related source evidence must be an array")
    for item in evidence:
        if (
            not isinstance(item, dict)
            or not required <= set(item) <= allowed
            or any(not isinstance(v, str) or any(ord(c) < 32 for c in v) for v in item.values())
            or not item["source_id"].strip()
        ):
            raise ValueError("complete related source citation required")
        _url(item["original_url"])
        if not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]):
            raise ValueError("related source SHA-256 required")


def validate_assertion(row: Mapping[str, str]) -> None:
    """Validate one scientific field decision and its original-document binding.

    Parameters
    ----------
    row : mapping of str to str
        Complete ledger row in ``COLUMNS``. Source dates do not describe events.

    Raises
    ------
    ValueError
        Columns, decision, source custody, rights, dates or precision are invalid.
    """
    if set(row) != set(COLUMNS) or any(
        not isinstance(value, str) or any(ord(c) < 32 for c in value) for value in row.values()
    ):
        raise ValueError("complete single-line research assertion required")
    if not row["stable_id"].strip() or row["field"] not in FIELDS:
        raise ValueError("research assertion identity or field is invalid")
    decision = row["selection"]
    if decision not in DECISIONS or not row["scope"].strip() or not row["assertion_basis"].strip():
        raise ValueError("explicit research decision and scope required")
    has_source = bool(row["source_id"])
    source_keys = (
        "source_title",
        "source_url",
        "source_sha256",
        "source_class",
        "locator",
        "rights",
    )
    if has_source:
        if any(not row[key].strip() for key in source_keys):
            raise ValueError("complete original-document citation required")
        _url(row["source_url"])
        if not re.fullmatch(r"[a-f0-9]{64}", row["source_sha256"]):
            raise ValueError("original-document SHA-256 required")
        if row["source_class"] not in NATIVE | {
            "tool_rendered_author_page_lead",
            "native_discovery_registry_json",
        }:
            raise ValueError("explicit original-source custody class required")
    elif any(row[key] for key in source_keys):
        raise ValueError("partial original-document citation refused")
    if decision == "selected":
        if not row["value"].strip() or not has_source or row["source_class"] not in NATIVE:
            raise ValueError("selected field requires a native original and a value")
    elif decision != "held" and row["value"]:
        raise ValueError("no-fill decision cannot supply a scalar value")
    if decision == "held" and row["value"] and not has_source:
        raise ValueError("held claim requires its source")
    _related(row["related_evidence"])
    _date(row["source_document_date"])
    _date(row["source_capture_date"])
    if row["field"] == "first_criticality" and row["value"]:
        _date(row["value"])
        precision = {4: "year", 7: "month", 10: "day"}[len(row["value"])]
        if row["date_precision"] != precision:
            raise ValueError("criticality precision differs from its value")
        if (
            decision == "selected"
            and len(row["source_capture_date"]) == 10
            and row["value"] > row["source_capture_date"]
        ):
            raise ValueError("future criticality cannot be selected as an actual event")
    elif row["date_precision"]:
        raise ValueError("event precision requires a criticality value")


def read_assertions(path: Path) -> tuple[dict[str, str], ...]:
    """Read a byte-preserved ledger without losing duplicate or malformed rows.

    Parameters
    ----------
    path : pathlib.Path
        Existing UTF-8 TSV with exactly ``COLUMNS``; aliases are refused.

    Returns
    -------
    tuple of dict of str to str
        Validated original ledger rows in their original order.

    Raises
    ------
    ValueError
        Columns, cells, identities or scientific/source contracts are invalid.
    OSError
        The original source cannot be read.
    """
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("research ledger symlinks are refused")
    reader = csv.DictReader(
        io.StringIO(path.read_bytes().decode("utf-8"), newline=""), delimiter="\t"
    )
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("exact research ledger columns required")
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for original in reader:
        if None in original or any(value is None for value in original.values()):
            raise ValueError("complete research ledger cells required")
        row = dict(original)
        validate_assertion(row)
        identity = (row["stable_id"], row["field"])
        if identity in seen:
            raise ValueError("duplicate research field decision refused")
        seen.add(identity)
        rows.append(row)
    return tuple(rows)


def project_fields(
    baseline: Mapping[str, Mapping[str, str]], assertions: Sequence[Mapping[str, str]]
) -> FieldProjection:
    """Apply a complete reviewed ledger only to originally blank scientific cells.

    Parameters
    ----------
    baseline : mapping of str to mapping of str to str
        Complete merged original cohort, keyed by the exact stable identity.
    assertions : sequence of mappings of str to str
        One explicit reviewed decision for every originally blank target field.
        Held and no-fill decisions remain evidence without changing cells.

    Returns
    -------
    FieldProjection
        Complete copied rows and exact selected/held/no-fill source assertions.

    Raises
    ------
    ValueError
        Identities, field coverage, review states or original values are unbound.
    """
    if not baseline or any(
        not identity.strip()
        or row.get("stable_id") != identity
        or any(field not in row for field in FIELDS)
        for identity, row in baseline.items()
    ):
        raise ValueError("complete exact-identity research baseline required")
    required = {
        (identity, field)
        for identity, row in baseline.items()
        for field in FIELDS
        if not row[field]
    }
    seen: set[tuple[str, str]] = set()
    rows = {identity: dict(row) for identity, row in baseline.items()}
    originals: list[dict[str, str]] = []
    for assertion in assertions:
        validate_assertion(assertion)
        key = (assertion["stable_id"], assertion["field"])
        if key not in required or key in seen:
            raise ValueError("research decision overwrites, duplicates or escapes its baseline")
        if assertion["selection"] == "unreviewed":
            raise ValueError("every missing research field requires an explicit review")
        seen.add(key)
        if assertion["selection"] == "selected":
            rows[key[0]][key[1]] = assertion["value"]
        originals.append(dict(assertion))
    if seen != required:
        raise ValueError("complete original missing-field cohort required")
    return FieldProjection(rows, tuple(originals))
