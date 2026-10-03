# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB source-bound presentation integration

"""Bind the complete FFDB source revision to its presentation-layer records."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from .build_from_ffdb import read_source_revision
from .catalogue import FIELDS, build_catalogue
from .values import DashboardRefused

LAYER = "05_global_reactor_map/imports/fusion/ffdb"
INPUTS = (
    f"{LAYER}/source_manifest.json",
    f"{LAYER}/fusion_facilities.tsv",
    f"{LAYER}/field_provenance.json",
    f"{LAYER}/visible_data.frames",
)


def build_facilities(
    root: Path,
    normalise_status: Callable[[str], str],
) -> list[dict[str, object]]:
    """Build source-bound presentation records from the complete pinned revision.

    Parameters
    ----------
    root : pathlib.Path
        Complete source tree, including the registered data selection and products.
    normalise_status : callable
        The presentation builder's actual status normaliser. Source status is
        retained separately, regardless of the display vocabulary.

    Returns
    -------
    list of dict
        Every FFDB catalogue identity, with only its source's map coordinates.

    Raises
    ------
    DashboardRefused
        If the data selection, products or source registry disagree, or cannot be read.
    """
    layer = root / LAYER
    dashboard, retrieved = read_source_revision(root / INPUTS[3], layer / "source_manifest.json")
    catalogue = build_catalogue(dashboard, retrieved)
    try:
        with (layer / "fusion_facilities.tsv").open(encoding="utf-8", newline="") as stream:
            table = csv.DictReader(stream, delimiter="\t")
            fields = table.fieldnames
            rows = list(table)
        provenance: object = json.loads(
            (layer / "field_provenance.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise DashboardRefused("FFDB source products cannot be read.") from None
    if fields != list(FIELDS) or rows != list(catalogue.rows) or provenance != catalogue.provenance:
        raise DashboardRefused("FFDB products differ from the complete registered source.")
    points = {point.identity: point for point in dashboard.map_points}
    records: list[dict[str, object]] = []
    for original, row in zip(dashboard.table, catalogue.rows, strict=True):
        point = points.get(original.identity)
        record: dict[str, object] = dict(row)
        record.update(
            {
                "id": "iaea-ffdb:" + hashlib.sha256(row["stable_id"].encode("utf-8")).hexdigest(),
                "lat": None if point is None else point.cells["Latitude"].raw,
                "lon": None if point is None else point.cells["Longitude"].raw,
                "domain": "fusion",
                "type": " / ".join((row["configuration"], row["device_subtype"])),
                "source_status": row["status"],
                "status": normalise_status(row["status"]),
                "evidence": "facility record",
                "record_kind": "fusion source catalogue record",
                "completeness": "partial" if point is not None else "unverified",
                "first_operation": "",
                "last_operation": "",
                "source_urls": [row["source_url"]],
                "source_checked": retrieved,
                "dataset_source": f"{LAYER}/fusion_facilities.tsv",
                "enrichment_applied": False,
                "data_caveat": row["verification_notes"],
                "ffdb_source_sha256": dashboard.source_sha256,
                "ffdb_original_response_sha256": dashboard.original_response_sha256,
                "ffdb_source_kind": dashboard.source_kind,
            }
        )
        records.append(record)
    return records
