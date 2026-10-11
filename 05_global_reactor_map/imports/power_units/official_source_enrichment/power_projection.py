# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — whole power-unit field projection
"""Project a complete author-curated ledger onto original blank power-unit cells."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_contract import (
    CONTEXT_FIELDS,
    DESIGN_ROLES,
    FIELDS,
    OPERATOR_ROLES,
    admit_citations,
    admit_sources,
    mapping,
    sequence,
    text,
)


@dataclass(frozen=True)
class PowerProjection:
    """Reconstructed original-order rows and their complete field decisions.

    Attributes
    ----------
    rows : tuple of dict
        Original string cells with qualified blank-cell values overlaid.
    decisions : tuple of dict
        All author dispositions, including held and bounded unknown cases.
    sources : tuple of dict
        Complete documentary custody and capture-attempt metadata.
    """

    rows: tuple[dict[str, str], ...]
    decisions: tuple[dict[str, object], ...]
    sources: tuple[dict[str, object], ...]


def admit_observations(value: object, sources: dict[str, dict[str, object]]) -> None:
    """Require every source-scope observation to retain its documents or attempts.

    Parameters
    ----------
    value : object
        Original array of author-inspected documentary scope observations.
    sources : dict
        Complete custody registry, with refused captures distinguished from documents.

    Raises
    ------
    ValueError
        An observation lacks meaning, provenance, or an explicitly retained attempt.
    """
    observations = sequence(value)
    if not observations:
        raise ValueError("power decision requires a source-scope observation")
    for item in observations:
        row = mapping(item)
        text(row, "basis")
        text(row, "scope")
        text(row, "candidate_value", empty=True)
        citations = admit_citations(row.get("citations"), sources, selected=False)
        attempts = sequence(row.get("capture_attempts"))
        seen: set[str] = set()
        for identity in attempts:
            if not isinstance(identity, str) or identity in seen:
                raise ValueError("power capture-attempt identity is invalid or duplicate")
            source = sources.get(identity)
            if source is None or source["body_state"] != "capture_attempt":
                raise ValueError("power capture-attempt reference lacks an attempt record")
            seen.add(identity)
        if not citations and not attempts:
            raise ValueError("power observation requires a document or a capture attempt")


def admit_decision(
    value: object,
    original: Mapping[str, str],
    sources: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Admit one blank-cell decision without replacing known fields or source stages.

    Parameters
    ----------
    value : object
        Exact field disposition, role, scope, citations and author observations.
    original : mapping
        Complete original string-valued power-unit row.
    sources : dict
        Complete custody registry admitted before field selection.

    Returns
    -------
    dict
        Original decision after documentary and unit-identity admission.

    Raises
    ------
    ValueError
        Identity, role, documentary support, rights or review status is inconsistent.
    """
    row = mapping(value)
    if text(row, "stable_id") != original["stable_id"]:
        raise ValueError("power decision targets a different original identity")
    field = text(row, "field")
    if field not in FIELDS or original[field] or row.get("original_value") != "":
        raise ValueError("power decision may only target an originally blank operator/type")
    context = mapping(row.get("original_context"))
    if context != {key: original[key] for key in CONTEXT_FIELDS}:
        raise ValueError("power decision context differs from the original unit")
    disposition = text(row, "disposition")
    selected = disposition == "qualified"
    if disposition not in {"qualified", "held", "unknown"}:
        raise ValueError("power decision is not a completed author disposition")
    scalar = text(row, "value", empty=True)
    role = text(row, "role", empty=True)
    if selected:
        permitted = OPERATOR_ROLES if field == "operator" else DESIGN_ROLES
        if not scalar.strip() or role not in permitted:
            raise ValueError("selected power value requires an explicit qualified field role")
    elif scalar or role:
        raise ValueError("held/unknown power decisions cannot fill a scalar or assign a role")
    text(row, "basis")
    text(row, "scope")
    citations = admit_citations(row.get("citations"), sources, selected=selected)
    if not selected and citations:
        raise ValueError("held/unknown power citations belong to observations, not selected claims")
    if row.get("author_review") != "completed" or "independent_review" not in row:
        raise ValueError(
            "power author review must be completed and separate from independent review"
        )
    if row["independent_review"] is not None:
        raise ValueError("power projection cannot infer an independent acceptance verdict")
    if row.get("rights_scope") != "citation_and_factual_metadata_only":
        raise ValueError("power field rights must exclude original body redistribution")
    admit_observations(row.get("observations"), sources)
    return row


def project_fields(
    baseline: Sequence[Mapping[str, str]], ledger: object, source_records: object
) -> PowerProjection:
    """Require the complete original gap set and project only qualified field values.

    Parameters
    ----------
    baseline : sequence of mapping
        Complete original rows, in source order, with all original strings.
    ledger : object
        One completed author decision for every originally blank operator/type cell.
    source_records : object
        Native-document and capture-attempt metadata, with explicit eligibility.

    Returns
    -------
    PowerProjection
        New row copies in original order and all qualified/held/unknown decisions.

    Raises
    ------
    ValueError
        The original rows or complete field set are malformed, duplicate or incomplete.
    """
    if not baseline:
        raise ValueError("power projection requires original rows")
    originals: dict[str, Mapping[str, str]] = {}
    for original in baseline:
        required = {"stable_id", *CONTEXT_FIELDS, *FIELDS}
        if not required.issubset(original) or any(
            not isinstance(cell, str) for cell in original.values()
        ):
            raise ValueError("power original row must retain all string-valued source cells")
        identity = original["stable_id"]
        if not identity or identity in originals:
            raise ValueError("power original identity is empty or duplicate")
        originals[identity] = original
    expected = {
        (identity, field)
        for identity, original in originals.items()
        for field in FIELDS
        if not original[field]
    }
    sources = admit_sources(source_records)
    decisions: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    projected = {identity: dict(original) for identity, original in originals.items()}
    for item in sequence(ledger):
        row = mapping(item)
        identity, field = text(row, "stable_id"), text(row, "field")
        key = (identity, field)
        if key not in expected or key in seen:
            raise ValueError("power ledger has an extra, known-field or duplicate target")
        decision = admit_decision(row, originals[identity], sources)
        seen.add(key)
        decisions.append(decision)
        if decision["disposition"] == "qualified":
            projected[identity][field] = text(decision, "value")
    if seen != expected:
        raise ValueError("power ledger omits original blank target fields")
    return PowerProjection(tuple(projected.values()), tuple(decisions), tuple(sources.values()))
