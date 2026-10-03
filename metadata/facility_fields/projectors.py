# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields source-specific projections

"""Keep each publisher's field meaning and native identity in a separate projection."""

from __future__ import annotations

import hashlib

from .inputs import NativeInput, text
from .observations import FieldObservation, identity, observation


def wri(source: NativeInput, target: NativeInput) -> list[FieldObservation]:
    """Retain all published primary and secondary whole-plant fuel categories.

    Parameters
    ----------
    source, target : NativeInput
        Complete original WRI CSV and its accepted plant table.

    Returns
    -------
    list of FieldObservation
        195 primary and six secondary categories, without material inference.
    """
    result = []
    for row in source.rows:
        if row["primary_fuel"] != "Nuclear":
            continue
        record_id = text(row["gppd_idnr"])
        for key in ("primary_fuel", "other_fuel1", "other_fuel2", "other_fuel3"):
            item = observation(
                source,
                target,
                target_id="wri-gppd-" + record_id.lower(),
                field="fuel_or_feed",
                value=row[key],
                basis="primary-fuel-classification"
                if key == "primary_fuel"
                else "secondary-fuel-classification",
                record_id=record_id,
                source_field=key,
            )
            if item is not None:
                result.append(item)
    return result


def agstar(source: NativeInput, target: NativeInput) -> list[FieldObservation]:
    """Retain published biogas end uses without inferring manure feed.

    Parameters
    ----------
    source, target : NativeInput
        Complete original AgSTAR source layer and accepted industrial table.

    Returns
    -------
    list of FieldObservation
        Nonblank original end uses; nullable identity components stay absent.
    """
    result = []
    for row in source.rows:
        fingerprint = "\x1f".join(
            str(row[k]).strip() if row[k] is not None else ""
            for k in ("Project_Na", "City", "State")
        ).casefold()
        target_id = "epa-agstar:" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
        item = observation(
            source,
            target,
            target_id=target_id,
            field="purpose",
            value=row["Biogas_End"],
            basis="published-end-use",
            record_id=identity(row["OBJECTID"]),
            source_field="Biogas_End",
        )
        if item is not None:
            result.append(item)
    return result


def bioenergy(
    source: NativeInput, target: NativeInput, snapshot: NativeInput
) -> list[FieldObservation]:
    """Retain EPE feedstocks or LMOP uses under the original native identity map.

    Parameters
    ----------
    source, target, snapshot : NativeInput
        Complete original native input, accepted layer and source identity table.

    Returns
    -------
    list of FieldObservation
        Original feedstocks or end-use categories, with no parsed plant-type inference.
    """
    field, native_field, basis = {
        "br-epe-biomethane": ("fuel_or_feed", "MateriaPri", "published-feedstock"),
        "us-epa-lmop": ("purpose", "project_type_category", "published-end-use"),
    }[source.key]
    identities = {
        (text(row["source"]), text(row["source_row_id"])): text(row["source_record_id"])
        for row in snapshot.rows
    }
    result = []
    for row in source.rows:
        oid = identity(row["OBJECTID"])
        item = observation(
            source,
            target,
            target_id=source.key + ":" + identities[(source.key, oid)],
            field=field,
            value=row[native_field],
            basis=basis,
            record_id=oid,
            source_field=native_field,
        )
        if item is not None:
            result.append(item)
    return result


def round7(source: NativeInput, target: NativeInput) -> list[FieldObservation]:
    """Keep Swiss valorisation distinct from Italian fuel classification.

    Parameters
    ----------
    source, target : NativeInput
        Complete reviewed source snapshot and its accepted discovery table.

    Returns
    -------
    list of FieldObservation
        All 153 published use labels and 268 fuel classifications.

    Raises
    ------
    ValueError
        A source namespace has not been reviewed.
    """
    registry = {text(row["stable_id"]): row for row in target.rows}
    result = []
    for row in source.rows:
        namespace, record_id = text(row["source"]), text(row["source_record_id"])
        if namespace not in {"ch-sfoe-biogas", "it-arpae-biogas"}:
            raise ValueError("unreviewed round-seven source namespace")
        swiss = namespace == "ch-sfoe-biogas"
        target_id = namespace + ":" + record_id
        original = registry[target_id]
        item = observation(
            source,
            target,
            target_id=target_id,
            field="purpose" if swiss else "fuel_or_feed",
            value=row["source_process_class"],
            basis="published-end-use" if swiss else "fuel-classification",
            record_id=record_id,
            source_field="source_process_class",
            source_url=text(original["source_url"]),
            checked=text(row["retrieved"]),
            license_id=text(row["license"]),
        )
        if item is not None:
            result.append(item)
    return result
