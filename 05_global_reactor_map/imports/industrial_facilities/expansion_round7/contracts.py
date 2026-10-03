# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — industrial round 7 observation contracts
"""Read verbatim source observations and validate their explicit data contract."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path
from typing import cast

HERE = Path(__file__).resolve().parent
MAX_BYTES = 8 * 1024 * 1024
SOURCES = {
    "ch-sfoe-biogas": ("Switzerland", "LicenseRef-opendata-swiss-terms-by"),
    "it-arpae-biogas": ("Italy", "CC-BY-4.0"),
}
SNAPSHOT_FIELDS = (
    "source source_record_id source_row_id facility_name operator country locality "
    "lat lon coordinate_basis source_process_class source_facility_class source_status "
    "capacity_electrical_mw capacity_thermal_mw capacity_chp_kw upgrading_capacity_m3_hour "
    "source_date source_beginning_operation source_context source_note source_biomass_note "
    "source_position_warning source_east source_north source_upgrading_technology retrieved license"
).split()
FIELDS = (
    "stable_id facility_name country lat lon precision sector process_or_activity "
    "reactor_type_if_explicit status operator capacity pollutant_or_product_context "
    "source_url source_role retrieved license verification_notes"
).split()


class ImportRefused(ValueError):
    """A deliberately authored refusal of an invalid source or output contract."""


def object_fields(value: object) -> dict[str, object]:
    """Require a JSON object without coercing another JSON type.

    Parameters
    ----------
    value : object
        A decoded publisher object.

    Returns
    -------
    dict of str to object
        Unmodified publisher members.

    Raises
    ------
    ImportRefused
        The value is not an object with string keys.
    """
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ImportRefused("source requires an object with string keys")
    return cast(dict[str, object], value)


def object_rows(value: object) -> list[dict[str, object]]:
    """Require a nonempty complete list of publisher objects.

    Parameters
    ----------
    value : object
        Decoded catalogue, resource or feature array.

    Returns
    -------
    list of dict
        Unmodified objects in publisher order.

    Raises
    ------
    ImportRefused
        The array or one of its rows is malformed.
    """
    if not isinstance(value, list) or not value:
        raise ImportRefused("source requires a nonempty object array")
    return [object_fields(row) for row in value]


def quantity(value: object, *, minimum: float, maximum: float) -> float:
    """Validate a finite published quantity without substituting for absence.

    Parameters
    ----------
    value : object
        Actual source number or numeric text; booleans and blanks are invalid.
    minimum, maximum : float
        Inclusive source or geographical bounds.

    Returns
    -------
    float
        Numeric value for validation and coordinate normalisation only.

    Raises
    ------
    ImportRefused
        The quantity has the wrong type, is not finite or is outside bounds.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ImportRefused("source quantity has the wrong type")
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise ImportRefused("source quantity is not numeric") from None
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ImportRefused("source quantity is not finite or is outside its bounds")
    return number


def _reject_constant(value: str) -> None:
    """Refuse a JSON nonfinite literal before it can enter a source observation."""
    raise ImportRefused("source JSON contains a nonfinite constant")


def read_json(path: Path) -> dict[str, object]:
    """Read a bounded regular publisher capture as a JSON object.

    Parameters
    ----------
    path : pathlib.Path
        Frozen native capture, never rewritten.

    Returns
    -------
    dict
        Decoded original members.

    Raises
    ------
    ImportRefused
        The capture is not bounded regular JSON or has a nonfinite constant.
    """
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ImportRefused("source capture must be a bounded regular file")
    try:
        value: object = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_constant
        )
    except (UnicodeError, ValueError):
        raise ImportRefused("source capture is not valid UTF-8 JSON") from None
    return object_fields(value)


def read_table(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read every verbatim TSV cell under an exact ordered schema.

    Parameters
    ----------
    path : pathlib.Path
        Frozen source snapshot or generated product.
    fields : list of str
        Required ordered column names.

    Returns
    -------
    list of dict
        Complete source cells without trimming or value replacement.

    Raises
    ------
    ImportRefused
        The file, column schema, row width or record set is invalid.
    """
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ImportRefused("table must be a bounded regular file")
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t", strict=True)
            if next(reader, []) != fields:
                raise ImportRefused("table header differs from its ordered contract")
            rows = list(reader)
    except (UnicodeError, csv.Error):
        raise ImportRefused("table is not valid UTF-8 tabular text") from None
    if not rows or any(len(row) != len(fields) for row in rows):
        raise ImportRefused("table is empty or has a malformed row")
    return [dict(zip(fields, row, strict=True)) for row in rows]


def check_observations(rows: list[dict[str, str]]) -> None:
    """Validate the complete observation set while preserving original cells.

    Parameters
    ----------
    rows : list of dict
        Rows under SNAPSHOT_FIELDS, from both permitted source namespaces.

    Raises
    ------
    ImportRefused
        A source, identity, licence, date, coordinate or quantity is invalid.
    """
    if not rows or any(set(row) != set(SNAPSHOT_FIELDS) for row in rows):
        raise ImportRefused("observation set is empty or its fields differ")
    identities: set[tuple[str, str]] = set()
    for row in rows:
        source = row["source"]
        if source not in SOURCES or (row["country"], row["license"]) != SOURCES[source]:
            raise ImportRefused("observation source, country or licence differs")
        identity = (source, row["source_record_id"].casefold())
        if not identity[1].strip() or identity in identities or not row["facility_name"].strip():
            raise ImportRefused("observation identity is missing or duplicated")
        identities.add(identity)
        try:
            retrieved = date.fromisoformat(row["retrieved"])
        except ValueError:
            raise ImportRefused("observation retrieval date is invalid") from None
        if retrieved > date.today() or not row["source_date"].strip():
            raise ImportRefused("observation date is future or source date is missing")
        quantity(row["lat"], minimum=-90, maximum=90)
        quantity(row["lon"], minimum=-180, maximum=180)
        for field in (
            "capacity_electrical_mw",
            "capacity_thermal_mw",
            "capacity_chp_kw",
            "upgrading_capacity_m3_hour",
        ):
            if row[field]:
                quantity(row[field], minimum=0, maximum=1_000_000_000)
        if source == "ch-sfoe-biogas":
            if row["capacity_electrical_mw"] or row["capacity_thermal_mw"]:
                raise ImportRefused(
                    "Swiss CHP capacity cannot acquire an electrical or thermal split"
                )
        elif row["capacity_chp_kw"] or row["upgrading_capacity_m3_hour"]:
            raise ImportRefused("Italian source does not publish Swiss capacity fields")


def main() -> None:
    """Inspect the complete frozen snapshot through a read-only native CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=HERE / "selected_source_snapshot.tsv")
    args = parser.parse_args()
    try:
        rows = read_table(args.snapshot, SNAPSHOT_FIELDS)
        check_observations(rows)
    except (OSError, ImportRefused):
        print("OBSERVATION CHECK FAILED: snapshot is missing or violates the source contract")
        raise SystemExit(1) from None
    print(
        f"{len(rows)} source observations; structural checks do not establish physical verification"
    )


if __name__ == "__main__":
    main()
