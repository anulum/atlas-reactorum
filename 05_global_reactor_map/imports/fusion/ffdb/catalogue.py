# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — source-specific FFDB catalogue

"""Build source-specific records without borrowing historical Fusion cells."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

from .reader import SOURCE_URL, TABLE_FIELDS, Dashboard, Record
from .values import DashboardRefused, number, text

FIELDS = (
    "stable_id",
    "name",
    "aliases",
    "country",
    "lat",
    "lon",
    "coordinate_precision",
    "configuration",
    "device_subtype",
    "status",
    "organization",
    "first_operation_date",
    "last_operation_date",
    "source_url",
    "source_role",
    "retrieved_date",
    "license",
    "verification_notes",
    "ownership",
    "design",
    "operator_website",
)
COORDINATE_NOTE = (
    "Publisher map location; facility/device granularity and precision are unspecified."
)


@dataclass(frozen=True)
class Catalogue:
    """Carry derived rows and the source-cell provenance required to audit them."""

    rows: tuple[dict[str, str], ...]
    provenance: dict[str, object]


def _source_id(record: Record) -> str:
    return "iaea-ffdb:" + "/".join(quote(value, safe="") for value in record.identity)


def _row(record: Record, point: Record | None, retrieved: str) -> dict[str, str]:
    raw = {field: text(record.cells[field].raw) for field in TABLE_FIELDS}
    website = "" if point is None else text(point.cells["Website"].raw)
    coordinates = (
        ("", "")
        if point is None
        else (
            str(number(point.cells["Latitude"].raw)),
            str(number(point.cells["Longitude"].raw)),
        )
    )
    return {
        "stable_id": _source_id(record),
        "name": raw["Facility Name"],
        "aliases": "",
        "country": raw["Country"],
        "lat": coordinates[0],
        "lon": coordinates[1],
        "coordinate_precision": "publisher map location; unspecified precision" if point else "",
        "configuration": raw["Configuration"],
        "device_subtype": raw["Type"],
        "status": raw["Status"],
        "organization": raw["Organization"],
        "first_operation_date": "",
        "last_operation_date": "",
        "source_url": SOURCE_URL,
        "source_role": "IAEA FFDB visible source catalogue",
        "retrieved_date": retrieved,
        "license": "IAEA FFDB source-specific reuse permission",
        "verification_notes": (
            "Dated publisher discovery record; no independent scientific approval. "
            + (COORDINATE_NOTE if point else "No coordinate supplied in the visible source map.")
        ),
        "ownership": raw["Ownership"],
        "design": raw["Design"],
        "operator_website": "" if website == "%null%" else website,
    }


def _provenance(record: Record, point: Record | None) -> dict[str, object]:
    fields: list[dict[str, object]] = [
        {
            "source_field": caption,
            "source_view": record.view,
            "source_tuple_id": record.tuple_id,
            "raw": cell.raw,
            "display": cell.display,
        }
        for caption, cell in record.cells.items()
    ]
    if point is not None:
        fields.extend(
            {
                "source_field": caption,
                "source_view": point.view,
                "source_tuple_id": point.tuple_id,
                "raw": point.cells[caption].raw,
                "display": point.cells[caption].display,
            }
            for caption in ("Latitude", "Longitude", "Website")
        )
    return {"stable_id": _source_id(record), "identity": list(record.identity), "fields": fields}


def build_catalogue(dashboard: Dashboard, retrieved_date: str) -> Catalogue:
    """Derive the complete source table with only its own map coordinates.

    Parameters
    ----------
    dashboard : Dashboard
        Complete views validated by the offline reader.
    retrieved_date : str
        ISO calendar date of the actual source capture, not an inspection date.

    Returns
    -------
    Catalogue
        Verbatim source classifications, explicit absences and bound provenance.

    Raises
    ------
    DashboardRefused
        If the capture date is not a canonical ISO calendar date.
    """
    try:
        checked = date.fromisoformat(retrieved_date)
    except ValueError:
        raise DashboardRefused("FFDB retrieval date must be an ISO calendar date.") from None
    if checked.isoformat() != retrieved_date:
        raise DashboardRefused("FFDB retrieval date must be an ISO calendar date.")
    if dashboard.retrieved_date is not None and dashboard.retrieved_date != retrieved_date:
        raise DashboardRefused("FFDB catalogue date differs from its source selection.")
    points = {point.identity: point for point in dashboard.map_points}
    rows = tuple(
        _row(record, points.get(record.identity), retrieved_date) for record in dashboard.table
    )
    provenance: dict[str, object] = {
        "schema_version": 1,
        "source_url": SOURCE_URL,
        "source_sha256": dashboard.source_sha256,
        "original_response_sha256": dashboard.original_response_sha256,
        "source_kind": dashboard.source_kind,
        "retrieved_date": retrieved_date,
        "publisher": "International Atomic Energy Agency",
        "source_permission": "FFDB-specific reuse with acknowledgement and no implied endorsement",
        "scientific_approval": False,
        "historical146_reconstructed": False,
        "stable_id_rule": "iaea-ffdb:percent-encoded exact facility/country/organisation identity",
        "coordinate_semantics": COORDINATE_NOTE,
        "records": [_provenance(record, points.get(record.identity)) for record in dashboard.table],
    }
    return Catalogue(rows, provenance)
