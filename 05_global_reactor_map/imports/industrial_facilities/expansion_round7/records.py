# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — industrial source-to-consumer projection
"""Project complete source observations without inferring reactor designs."""

from __future__ import annotations

from collections import Counter

from .capture import ARPAE_SERVICE, SFOE_URL
from .contracts import FIELDS, ImportRefused, check_observations

EXPECTED = {"ch-sfoe-biogas": 153, "it-arpae-biogas": 268}
SOURCE_URLS = {"ch-sfoe-biogas": SFOE_URL, "it-arpae-biogas": ARPAE_SERVICE + "/0"}
CAPACITIES = {
    "capacity_electrical_mw": "electrical capacity (MW)",
    "capacity_thermal_mw": "thermal capacity (MW)",
    "capacity_chp_kw": "CHP capacity (kW; electrical/thermal split unpublished)",
    "upgrading_capacity_m3_hour": "gas upgrading capacity (m3/hour)",
}
NOTE_FIELDS = {
    "source_row_id": "native row ID",
    "locality": "source locality",
    "coordinate_basis": "source coordinate basis",
    "source_date": "source reference/update text",
    "source_beginning_operation": "source beginning-of-operation year",
    "source_note": "source note",
    "source_biomass_note": "source biomass note",
    "source_position_warning": "publisher position warning",
    "source_east": "native easting",
    "source_north": "native northing",
    "source_upgrading_technology": "source upgrading technology",
}


def project_rows(observations: list[dict[str, str]]) -> list[dict[str, str]]:
    """Project every selected observation under the complete consumer schema.

    Parameters
    ----------
    observations : list of dict
        All 153 Swiss and 268 Italian reviewed observations, retaining raw cells.

    Returns
    -------
    list of dict
        Deterministically ordered 18-field facility discovery records.

    Raises
    ------
    ImportRefused
        A source contract, reviewed count or native identity is incomplete.
    """
    check_observations(observations)
    if Counter(row["source"] for row in observations) != EXPECTED:
        raise ImportRefused("observation set differs from the reviewed complete source counts")
    records: list[dict[str, str]] = []
    for row in observations:
        identity = row["source_record_id"]
        if (
            not row["source_row_id"].strip()
            or not row["coordinate_basis"].strip()
            or any(character.isspace() or character in ":/\\" for character in identity)
        ):
            raise ImportRefused("native identity or coordinate provenance is invalid")
        swiss = row["source"] == "ch-sfoe-biogas"
        classification = "source valorization" if swiss else "source fuel"
        notes = (
            "Facility discovery record; vessel count, reactor design and current operation "
            "are not independently verified."
        )
        for field, label in NOTE_FIELDS.items():
            if row[field]:
                notes += f" | {label}: {row[field]}"
        record = dict.fromkeys(FIELDS, "")
        record.update(
            stable_id=row["source"] + ":" + identity,
            facility_name=row["facility_name"],
            country=row["country"],
            lat=row["lat"],
            lon=row["lon"],
            precision="Source point; publisher requests position verification"
            if row["source_position_warning"]
            else "Source point; positional accuracy unverified",
            sector="bioenergy facility",
            process_or_activity=(
                f"Source facility class: {row['source_facility_class']}; "
                f"{classification}: {row['source_process_class']}"
            ),
            status=row["source_status"],
            operator=row["operator"],
            capacity="; ".join(
                f"{label}: {row[field]}" for field, label in CAPACITIES.items() if row[field]
            ),
            pollutant_or_product_context=row["source_context"],
            source_url=SOURCE_URLS[row["source"]],
            source_role="official_dataset",
            retrieved=row["retrieved"],
            license=row["license"],
            verification_notes=notes,
        )
        records.append(record)
    return sorted(records, key=lambda record: record["stable_id"])
