#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 04_interactive_presentation/scripts/build_datasets.py
"""Build offline atlas assets from source TSVs without network access.

Run from any directory. Output is deterministic; upstream metadata is preserved.
"""

import argparse
import csv
import hashlib
import importlib
import json
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from metadata.facility_fields.runtime import MEMBERS as FIELD_MEMBERS
from metadata.facility_fields.runtime import apply_fields

PRESENTATION = Path(__file__).resolve().parents[1]
LIBRARY = PRESENTATION.parent
DATA = PRESENTATION / "data"
FACILITY_SOURCE = LIBRARY / "05_global_reactor_map/data/reactors.tsv"
COMPANY_SOURCE = LIBRARY / "metadata/discovery_audit/fusion_companies_candidates.tsv"
COMPANY_AUDIT_SOURCE = LIBRARY / "metadata/company_audit/audited_companies.tsv"
COMPANY_EXPANSION_SOURCE = LIBRARY / "metadata/company_audit/expansion_candidates.tsv"
COMPANY_EXPANSION_ROUND2_SOURCE = LIBRARY / "metadata/company_audit/expansion_round2/candidates.tsv"
COMPANY_EXPANSION_ROUND3_SOURCE = LIBRARY / "metadata/company_audit/expansion_round3/candidates.tsv"
COMPANY_DEPTH_OVERLAY_SOURCE = (
    LIBRARY / "metadata/company_audit/depth_round4/enrichment_overlays.tsv"
)
COMPANY_DEPTH_MATRIX_SOURCE = LIBRARY / "metadata/company_audit/depth_round4/gap_matrix.tsv"
COMPANY_DEPTH_ROUND5_SOURCE = (
    LIBRARY / "metadata/company_audit/depth_round5/enrichment_overlays.tsv"
)
COMPANY_DEPTH_ROUND6_SOURCE = (
    LIBRARY / "metadata/company_audit/depth_round6/enrichment_overlays.tsv"
)
COMPANY_DEPTH_ROUND7_SOURCE = (
    LIBRARY / "metadata/company_audit/depth_round7/enrichment_overlays.tsv"
)
COMPANY_DEPTH_ROUND8_SOURCE = (
    LIBRARY / "metadata/company_audit/depth_round8/enrichment_overlays.tsv"
)
SUPPLEMENT = DATA / "facilities-supplemental.json"
# Bumped when the published record shape changes.
SCHEMA_VERSION = "1.0.0"
FUSION_SOURCE = LIBRARY / "05_global_reactor_map/imports/fusion/fusion_facilities.tsv"
FUSION_ENRICHMENT_SOURCE = (
    LIBRARY / "05_global_reactor_map/imports/fusion/enrichment/enrichment.tsv"
)
FUSION_ENRICHMENT_ROUND2_SOURCE = (
    LIBRARY / "05_global_reactor_map/imports/fusion/enrichment_round2/enrichment_round2.tsv"
)
FUSION_ENRICHMENT_ROUND3_SOURCE = (
    LIBRARY / "05_global_reactor_map/imports/fusion/enrichment_round3/enrichment_round3.tsv"
)
FUSION_NEW_SOURCE = LIBRARY / "05_global_reactor_map/imports/fusion/enrichment/new_facilities.tsv"
RESEARCH_SOURCE = LIBRARY / "05_global_reactor_map/imports/research_reactors/research_reactors.tsv"
RESEARCH_ENRICHMENT_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/research_reactors/enrichment/research_reactor_enrichment.tsv"
)
RESEARCH_ENRICHMENT_ROUND2_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/research_reactors/enrichment_round2/research_reactor_enrichment_round2.tsv"
)
RESEARCH_ENRICHMENT_ROUND3_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/research_reactors/enrichment_round3/research_reactor_enrichment_round3.tsv"
)
RESEARCH_ENRICHMENT_ROUND4_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/research_reactors/enrichment_round4/research_reactor_enrichment_round4.tsv"
)
RESEARCH_ENRICHMENT_ROUND5_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/research_reactors/enrichment_round5/research_reactor_enrichment_round5.tsv"
)
POWER_UNIT_SOURCE = LIBRARY / "05_global_reactor_map/imports/power_units/power_reactor_units.tsv"
INDUSTRIAL_SOURCE = (
    LIBRARY / "05_global_reactor_map/imports/industrial_facilities/industrial_facilities.tsv"
)
INDUSTRIAL_ROUND2_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round2/industrial_facilities_round2.tsv"
)
INDUSTRIAL_ROUND3_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round3/industrial_facilities_round3.tsv"
)
INDUSTRIAL_ROUND4_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round4/industrial_facilities_round4.tsv"
)
INDUSTRIAL_ROUND5_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round5/industrial_facilities_round5.tsv"
)
INDUSTRIAL_ROUND6_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round6/industrial_facilities_round6.tsv"
)
INDUSTRIAL_ROUND7_SOURCE = (
    LIBRARY
    / "05_global_reactor_map/imports/industrial_facilities/expansion_round7/industrial_facilities_round7.tsv"
)
INDUSTRIAL_ROUND7_VALIDATOR = importlib.import_module(
    "05_global_reactor_map.imports.industrial_facilities.expansion_round7.validate"
)
FFDB_INTEGRATION = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.integration")
HISTORICAL_INPUTS = importlib.import_module(
    "05_global_reactor_map.imports.fusion.historical_inputs"
)
RESEARCH_INTEGRATION = importlib.import_module(
    "05_global_reactor_map.imports.research_reactors.official_source_enrichment.integration"
)
PRIMARY_RESEARCH = importlib.import_module(
    "05_global_reactor_map.imports.research_reactors.official_source_enrichment.primary_integration"
)
FUSION_SNAPSHOT: Path | None = None


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Read a tab-separated source file into rows.

    Parameters
    ----------
    path : pathlib.Path
        The TSV file to read.

    Returns
    -------
    list of dict
        One mapping of column name to raw value per row, read verbatim.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


_SOURCE_DEFAULTS = {
    "FACILITY_SOURCE": FACILITY_SOURCE,
    "COMPANY_SOURCE": COMPANY_SOURCE,
    "COMPANY_AUDIT_SOURCE": COMPANY_AUDIT_SOURCE,
    "COMPANY_EXPANSION_SOURCE": COMPANY_EXPANSION_SOURCE,
    "COMPANY_EXPANSION_ROUND2_SOURCE": COMPANY_EXPANSION_ROUND2_SOURCE,
    "COMPANY_EXPANSION_ROUND3_SOURCE": COMPANY_EXPANSION_ROUND3_SOURCE,
    "COMPANY_DEPTH_OVERLAY_SOURCE": COMPANY_DEPTH_OVERLAY_SOURCE,
    "COMPANY_DEPTH_MATRIX_SOURCE": COMPANY_DEPTH_MATRIX_SOURCE,
    "COMPANY_DEPTH_ROUND5_SOURCE": COMPANY_DEPTH_ROUND5_SOURCE,
    "COMPANY_DEPTH_ROUND6_SOURCE": COMPANY_DEPTH_ROUND6_SOURCE,
    "COMPANY_DEPTH_ROUND7_SOURCE": COMPANY_DEPTH_ROUND7_SOURCE,
    "COMPANY_DEPTH_ROUND8_SOURCE": COMPANY_DEPTH_ROUND8_SOURCE,
    "FUSION_SOURCE": FUSION_SOURCE,
    "FUSION_ENRICHMENT_SOURCE": FUSION_ENRICHMENT_SOURCE,
    "FUSION_ENRICHMENT_ROUND2_SOURCE": FUSION_ENRICHMENT_ROUND2_SOURCE,
    "FUSION_ENRICHMENT_ROUND3_SOURCE": FUSION_ENRICHMENT_ROUND3_SOURCE,
    "FUSION_NEW_SOURCE": FUSION_NEW_SOURCE,
    "RESEARCH_SOURCE": RESEARCH_SOURCE,
    "RESEARCH_ENRICHMENT_SOURCE": RESEARCH_ENRICHMENT_SOURCE,
    "RESEARCH_ENRICHMENT_ROUND2_SOURCE": RESEARCH_ENRICHMENT_ROUND2_SOURCE,
    "RESEARCH_ENRICHMENT_ROUND3_SOURCE": RESEARCH_ENRICHMENT_ROUND3_SOURCE,
    "RESEARCH_ENRICHMENT_ROUND4_SOURCE": RESEARCH_ENRICHMENT_ROUND4_SOURCE,
    "RESEARCH_ENRICHMENT_ROUND5_SOURCE": RESEARCH_ENRICHMENT_ROUND5_SOURCE,
    "POWER_UNIT_SOURCE": POWER_UNIT_SOURCE,
    "INDUSTRIAL_SOURCE": INDUSTRIAL_SOURCE,
    "INDUSTRIAL_ROUND2_SOURCE": INDUSTRIAL_ROUND2_SOURCE,
    "INDUSTRIAL_ROUND3_SOURCE": INDUSTRIAL_ROUND3_SOURCE,
    "INDUSTRIAL_ROUND4_SOURCE": INDUSTRIAL_ROUND4_SOURCE,
    "INDUSTRIAL_ROUND5_SOURCE": INDUSTRIAL_ROUND5_SOURCE,
    "INDUSTRIAL_ROUND6_SOURCE": INDUSTRIAL_ROUND6_SOURCE,
    "INDUSTRIAL_ROUND7_SOURCE": INDUSTRIAL_ROUND7_SOURCE,
}


def configure_roots(source_root: Path, data_dir: Path) -> None:
    """Point every source and output path at the given roots.

    Parameters
    ----------
    source_root : pathlib.Path
        Root the source catalogues are read from.
    data_dir : pathlib.Path
        Directory the generated datasets are written to.

    Notes
    -----
    Exposed so tests can run this script as a real process against a real
    directory tree, rather than substituting module attributes.
    """
    global LIBRARY, DATA, SUPPLEMENT, FUSION_SNAPSHOT
    FUSION_SNAPSHOT = None
    relative = {name: value.relative_to(LIBRARY) for name, value in _SOURCE_DEFAULTS.items()}
    LIBRARY = source_root
    DATA = data_dir
    SUPPLEMENT = data_dir / "facilities-supplemental.json"
    for name, rel in relative.items():
        globals()[name] = source_root / rel


def configure_historical_snapshot(directory: Path) -> None:
    """Point historical consumers at verified owned input bytes.

    Parameters
    ----------
    directory : pathlib.Path
        Private snapshot created after all nine source hashes and schemas pass.
    """
    global FUSION_SOURCE, FUSION_NEW_SOURCE, FUSION_SNAPSHOT
    global \
        FUSION_ENRICHMENT_SOURCE, \
        FUSION_ENRICHMENT_ROUND2_SOURCE, \
        FUSION_ENRICHMENT_ROUND3_SOURCE
    FUSION_SNAPSHOT = directory
    FUSION_SOURCE = directory / "fusion_facilities.tsv"
    FUSION_NEW_SOURCE = directory / "enrichment/new_facilities.tsv"
    FUSION_ENRICHMENT_SOURCE = directory / "enrichment/enrichment.tsv"
    FUSION_ENRICHMENT_ROUND2_SOURCE = directory / "enrichment_round2/enrichment_round2.tsv"
    FUSION_ENRICHMENT_ROUND3_SOURCE = directory / "enrichment_round3/enrichment_round3.tsv"


def _relative_label(path: Path) -> str:
    """Describe a path relative to the source root where that is meaningful.

    Generated datasets may live outside the source tree, so a plain
    ``relative_to`` would raise rather than label them. The file name is then
    the honest label: it identifies the artefact without claiming a location
    inside a tree it does not belong to.

    Parameters
    ----------
    path : pathlib.Path
        The path to label.

    Returns
    -------
    str
        A repository-relative path, or the file name when the path lies
        outside the source root.
    """
    if FUSION_SNAPSHOT is not None and path.is_relative_to(FUSION_SNAPSHOT):
        return (
            "05_global_reactor_map/imports/fusion/" + path.relative_to(FUSION_SNAPSHOT).as_posix()
        )
    try:
        return str(path.relative_to(LIBRARY))
    except ValueError:
        return path.name


def _records_of(document: Any) -> list[dict[str, Any]]:
    """Return the record list from a dataset document.

    Parameters
    ----------
    document : Any
        A parsed dataset, either the wrapped object form or a bare array.

    Returns
    -------
    list of dict
        The records it carries.
    """
    if isinstance(document, dict):
        records: list[dict[str, Any]] = document["records"]
        return records
    bare: list[dict[str, Any]] = document
    return bare


def emit(
    name: str,
    variable: str,
    records: list[dict[str, Any]],
    data_dir: Path | None = None,
    *,
    schema_version: str = SCHEMA_VERSION,
) -> None:
    """Write a dataset as both JSON and a browser-loadable JavaScript file.

    Parameters
    ----------
    name : str
        Base filename, without extension.
    variable : str
        Global name the JavaScript file assigns to.
    records : list of dict
        The records to serialise.
    data_dir : pathlib.Path or None
        Directory to write into. Defaults to the configured output directory.

    schema_version : str
        Record-shape revision; complete primary research uses 1.3.0, historical
        research without the bundle uses 1.2.0, and companies retain 1.0.0.

    Notes
    -----
    The JavaScript form exists because the atlas must load over ``file://``,
    where `fetch` of a sibling JSON file is blocked.
    """
    # The Tier-0 scaffold profile requires every repository JSON file to have an
    # object at its top level, so the record array is wrapped. The wrapper
    # carries only deterministic fields: a build that embedded a timestamp
    # would stop reproducing byte for byte.
    document = {"schema_version": schema_version, "record_count": len(records), "records": records}
    serialized = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    target = data_dir if data_dir is not None else DATA
    (target / f"{name}.json").write_text(serialized, encoding="utf-8")
    # External JS works both over HTTP and when index.html is opened as a file.
    (target / f"{name}.js").write_text(
        f"window.{variable} = {serialized.rstrip()};\n", encoding="utf-8"
    )


def nullable_number(value: str | None) -> float | None:
    """Parse an optional numeric field.

    Parameters
    ----------
    value : str or None
        The raw source value.

    Returns
    -------
    float or None
        The parsed number, or None when the source supplied nothing. An absent
        value is never coerced to zero, which would invent a measurement.
    """
    text = (value or "").strip()
    return float(text) if text else None


def normalize_status(value: str | None) -> str:
    """Collapse source status vocabularies onto the atlas status set.

    Parameters
    ----------
    value : str or None
        The raw source status.

    Returns
    -------
    str
        The mapped status, or the lower-cased source value when no mapping
        applies. The field name mirrors the published ``normalized_status``
        schema key and is therefore not re-spelled.
    """
    # A whitespace-only status is as absent as an empty one; without the
    # strip first, " " is truthy and bypasses the fallback, yielding "".
    raw = (value or "").strip() or "unknown"
    key = raw.lower().replace("_", " ")
    if key.startswith("operating"):
        return "operational"
    if key.startswith("shut down"):
        return "shutdown"
    if key.startswith("commissioning"):
        return "commissioning"
    return key


def normalized_id(value: str) -> str:
    """Create a UI-safe key while retaining the source stable_id separately.

    Parameters
    ----------
    value : str
        The source identifier.

    Returns
    -------
    str
        A key safe for use in DOM attributes and query strings.
    """
    return re.sub(r"[^a-z0-9:._-]+", "_", value.lower()).strip("_")


COUNTRY_ALIASES = {
    "": "Unknown",
    "unknown": "Unknown",
    "EG": "Egypt",
    "LY": "Libya",
    "Czechia": "Czech Republic",
    "People's Republic of China": "China",
    "Türkiye": "Turkey",
    "United States of America": "United States",
}


def normalize_country(value: str | None) -> str:
    """Collapse exact source aliases for UI filtering without losing provenance.

    Parameters
    ----------
    value : str or None
        The raw source country value.

    Returns
    -------
    str
        The display country. The original source value is retained separately
        as ``source_country`` so no provenance is lost.
    """
    raw = (value or "").strip()
    return COUNTRY_ALIASES.get(raw, raw or "Unknown")


def build_base_facilities(source: Path) -> list[dict[str, Any]]:
    """Build the base facility layer from the primary reactor catalogue.

    Parameters
    ----------
    source : pathlib.Path
        The primary reactor catalogue.

    Returns
    -------
    list of dict
        One record per catalogue row, in source order.

    Raises
    ------
    ValueError
        When a row carries a coordinate outside the geographic domain.
    """
    facilities: list[dict[str, Any]] = []
    for row in read_tsv(source):
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"coordinate out of range for {row['id']}")
        facilities.append(
            {
                **row,
                "lat": lat,
                "lon": lon,
                "domain": "fission",
                "type": row["reactor_type"],
                "evidence": row["evidence_maturity"],
                "completeness": "partial",
                "record_kind": "plant-level source record",
                "upstream_record_kind": row["record_kind"],
                "source_checked": row["last_verified"],
                "dataset_source": "05_global_reactor_map/data/reactors.tsv",
                "data_caveat": "Plant-level source record, not an independently verified reactor-unit record. Status, reactor design and coordinate precision are unknown in this dataset. Source dates do not establish present operation.",
            }
        )
    # Supplemental research and fusion facilities are retained, but the original
    # sample's verified-location assertion is not promoted to a new audit claim.
    for original in _records_of(json.loads(SUPPLEMENT.read_text(encoding="utf-8"))):
        row = dict(original)
        row.update(
            {
                "original_completeness": original["completeness"],
                "completeness": "context-only"
                if original["completeness"] == "context-only"
                else "partial",
                "record_kind": "context facility"
                if original["completeness"] == "context-only"
                else "supplemental facility",
                "dataset_source": "04_interactive_presentation/data/facilities-supplemental.json",
                "data_caveat": "Original prototype record; approximate coordinates and status have not been independently rechecked during dataset integration.",
            }
        )
        facilities.append(row)
    return facilities


def build_fusion_facilities(
    source: Path,
    enrichment_sources: Sequence[Path],
    new_source: Path,
) -> list[dict[str, Any]]:
    """Build the fusion device layer and fold its enrichment rounds in.

    Parameters
    ----------
    source : pathlib.Path
        The base fusion device catalogue.
    enrichment_sources : sequence of pathlib.Path
        Exact-identifier enrichment rounds, applied in order. A round that
        is not present is skipped, which is how a partial checkout behaves.
    new_source : pathlib.Path
        Official-source additions not present in the base catalogue.

    Returns
    -------
    list of dict
        The fusion records this layer contributes.
    """
    records: list[dict[str, Any]] = []
    if source.exists():
        fusion_enrichments: dict[str, dict[str, str]] = {}
        fusion_enrichment_urls: dict[str, list[str]] = {}
        for enrichment_source in enrichment_sources:
            if enrichment_source.exists():
                for enrichment in read_tsv(enrichment_source):
                    sid = enrichment["stable_id"]
                    fusion_enrichments[sid] = {
                        **fusion_enrichments.get(sid, {}),
                        **{key: value for key, value in enrichment.items() if value},
                    }
                    fusion_enrichment_urls.setdefault(sid, []).extend(
                        url.strip()
                        for url in enrichment.get("source_url", "").split(" | ")
                        if url.strip()
                    )
        fusion_input_rows = [(row, False) for row in read_tsv(source)]
        if new_source.exists():
            fusion_input_rows.extend((row, True) for row in read_tsv(new_source))
        for source_row, is_new in fusion_input_rows:
            patch = fusion_enrichments.get(source_row["stable_id"])
            row = {
                **source_row,
                **({key: value for key, value in patch.items() if value} if patch else {}),
            }
            opt_lat: float | None = nullable_number(row.get("lat") or row.get("latitude"))
            opt_lon = nullable_number(row.get("lon") or row.get("longitude"))
            source_urls: list[str] = []
            for value in (source_row.get("source_url"),):
                source_urls.extend(url.strip() for url in (value or "").split(" | ") if url.strip())
            source_urls.extend(fusion_enrichment_urls.get(source_row["stable_id"], []))
            source_urls = list(dict.fromkeys(source_urls))
            records.append(
                {
                    **row,
                    "id": row.get("id") or row["stable_id"],
                    "name": row["name"],
                    "country": row.get("country") or "Unknown",
                    "lat": opt_lat,
                    "lon": opt_lon,
                    "domain": "fusion",
                    "type": " / ".join(
                        filter(None, [row.get("configuration"), row.get("device_subtype")])
                    ),
                    "source_status": row.get("status") or "unknown",
                    "status": normalize_status(row.get("status")),
                    "evidence": "facility record",
                    "record_kind": "fusion device",
                    "completeness": "partial"
                    if opt_lat is not None and opt_lon is not None
                    else "unverified",
                    "organization": row.get("organization", ""),
                    "first_operation": row.get("first_operation_date", ""),
                    "last_operation": row.get("last_operation_date", ""),
                    "source_url": source_urls[-1],
                    "source_urls": source_urls,
                    "source_checked": row.get("retrieved_date") or row.get("retrieved"),
                    "dataset_source": (
                        "05_global_reactor_map/imports/fusion/enrichment/new_facilities.tsv"
                        if is_new
                        else "05_global_reactor_map/imports/fusion/fusion_facilities.tsv"
                    ),
                    "enrichment_applied": bool(patch) or is_new,
                    "data_caveat": row.get("verification_evidence_notes")
                    or row.get("verification_notes")
                    or "Discovery record; verify status and coordinates against the current operator.",
                }
            )
    return records


def build_research_facilities(
    source: Path,
    enrichment_sources: Sequence[Path],
) -> list[dict[str, Any]]:
    """Build the research-reactor layer and fold its enrichment rounds in.

    Parameters
    ----------
    source : pathlib.Path
        The base research-reactor catalogue.
    enrichment_sources : sequence of pathlib.Path
        Exact-identifier enrichment rounds, applied in order. Absent rounds
        are skipped rather than treated as empty overlays.

    Returns
    -------
    list of dict
        The research-reactor records this layer contributes.
    """
    records: list[dict[str, Any]] = []
    merged_rows: dict[str, dict[str, str]] = {}
    if source.exists():
        base = RESEARCH_INTEGRATION.read_layer(source, LIBRARY)
        layers = [
            RESEARCH_INTEGRATION.read_layer(path, LIBRARY)
            for path in enrichment_sources
            if path.exists()
        ]
        for source_row in base.rows.values():
            row, source_urls, origins, applied = RESEARCH_INTEGRATION.merge_layers(
                source_row, base, layers
            )
            merged_rows[row["stable_id"]] = row
            opt_lat, opt_lon = nullable_number(row.get("lat")), nullable_number(row.get("lon"))
            records.append(
                {
                    **row,
                    "id": row.get("id") or row["stable_id"],
                    "name": row["name"],
                    "country": row.get("country") or "Unknown",
                    "lat": opt_lat,
                    "lon": opt_lon,
                    "domain": "fission",
                    "type": row.get("reactor_type") or "research reactor",
                    "source_status": row.get("status") or "unknown",
                    "status": normalize_status(row.get("status")),
                    "evidence": "facility record",
                    "record_kind": "research reactor",
                    "completeness": "partial"
                    if opt_lat is not None and opt_lon is not None
                    else "unverified",
                    "source_url": source_urls[-1],
                    "source_urls": source_urls,
                    "source_checked": row.get("retrieved") or row.get("retrieved_date"),
                    "dataset_source": "05_global_reactor_map/imports/research_reactors/research_reactors.tsv",
                    "enrichment_applied": applied,
                    **({"research_field_origins": origins} if origins else {}),
                    "data_caveat": row.get("verification_notes")
                    or "Discovery record; verify status and coordinates against the current regulator or operator.",
                }
            )
    projection = PRIMARY_RESEARCH.load_projection(
        merged_rows, source.parent / "official_source_enrichment"
    )
    if projection is not None:
        assertions_by_identity: dict[str, list[dict[str, str]]] = {}
        for assertion in projection.assertions:
            assertions_by_identity.setdefault(assertion["stable_id"], []).append(assertion)
        for record in records:
            identity = record["stable_id"]
            for field in ("operator", "purpose", "first_criticality"):
                record[field] = projection.rows[identity][field]
            assertions = assertions_by_identity.get(identity, [])
            if assertions:
                record["research_primary_assertions"] = assertions
                citations = [row["source_url"] for row in assertions if row["source_url"]]
                record["source_urls"] = list(dict.fromkeys([*record["source_urls"], *citations]))
    return records


def build_power_unit_facilities(source: Path) -> list[dict[str, Any]]:
    """Build the power-reactor unit layer.

    Parameters
    ----------
    source : pathlib.Path
        The power-reactor unit catalogue.

    Returns
    -------
    list of dict
        The unit-level records this layer contributes. These are reactor
        units, unlike the plant-level rows in the base layer.
    """
    records: list[dict[str, Any]] = []
    if source.exists():
        for row in read_tsv(source):
            opt_lat = nullable_number(row.get("lat") or row.get("latitude"))
            opt_lon = nullable_number(row.get("lon") or row.get("longitude"))
            source_urls = [url.strip() for url in row["source_url"].split("|") if url.strip()]
            records.append(
                {
                    **row,
                    "id": normalized_id(row.get("stable_id") or row["id"]),
                    "name": row.get("unit_name") or row.get("plant_name") or row["stable_id"],
                    "country": row.get("country") or "Unknown",
                    "lat": opt_lat,
                    "lon": opt_lon,
                    "domain": "fission",
                    "type": " / ".join(filter(None, [row.get("reactor_type"), row.get("model")])),
                    "source_status": row.get("status") or "unknown",
                    "status": normalize_status(row.get("status")),
                    "evidence": "facility record",
                    "record_kind": "power reactor unit",
                    "completeness": "partial"
                    if opt_lat is not None and opt_lon is not None
                    else "unverified",
                    "source_url": source_urls[0],
                    "source_urls": source_urls,
                    "source_checked": row.get("retrieved") or row.get("retrieved_date"),
                    "dataset_source": "05_global_reactor_map/imports/power_units/power_reactor_units.tsv",
                    "data_caveat": row.get("verification_notes")
                    or "Open unit-level discovery record; verify current status and technical values against the regulator and operator.",
                }
            )
    return records


def build_industrial_facilities(sources: Sequence[Path]) -> list[dict[str, Any]]:
    """Build the industrial and process-site layer from its expansion rounds.

    Parameters
    ----------
    sources : sequence of pathlib.Path
        Expansion rounds, applied in order. An absent round is skipped; any
        present round-seven artifact requires its complete source-bound bundle.

    Returns
    -------
    list of dict
        The industrial records these rounds contribute. A record here
        identifies a regulated site or project, not a reactor vessel.
    """
    records: list[dict[str, Any]] = []
    for industrial_source in sources:
        if industrial_source == INDUSTRIAL_ROUND7_SOURCE:
            INDUSTRIAL_ROUND7_VALIDATOR.validate_optional_bundle(
                industrial_source.parent,
                previous_layers=tuple(
                    path for path in sources if path != industrial_source and path.exists()
                ),
            )
        if not industrial_source.exists():
            continue
        for row in read_tsv(industrial_source):
            opt_lat = nullable_number(row.get("lat") or row.get("latitude"))
            opt_lon = nullable_number(row.get("lon") or row.get("longitude"))
            records.append(
                {
                    **row,
                    "id": normalized_id(row.get("stable_id") or row["id"]),
                    "name": row.get("facility_name") or row.get("name"),
                    "country": row.get("country") or "Unknown",
                    "lat": opt_lat,
                    "lon": opt_lon,
                    "domain": "chemical",
                    "type": row.get("reactor_type_if_explicit")
                    or row.get("process_or_activity")
                    or row.get("sector")
                    or "industrial process facility",
                    "source_status": row.get("status") or "unknown",
                    "status": normalize_status(row.get("status")),
                    "evidence": "facility record",
                    "record_kind": "industrial process facility",
                    "completeness": "partial"
                    if opt_lat is not None and opt_lon is not None
                    else "unverified",
                    "source_url": row["source_url"],
                    "source_checked": row.get("retrieved") or row.get("retrieved_date"),
                    "dataset_source": str(industrial_source.relative_to(LIBRARY)),
                    "data_caveat": row.get("verification_notes")
                    or "Public facility/process record; it does not identify individual reactor vessels unless explicitly stated.",
                }
            )
    return records


def build_companies() -> list[dict[str, Any]]:
    """Build the company and programme layer with its audit overlays.

    Returns
    -------
    list of dict
        One record per audited company or programme. Company claims, the
        highest independently supported milestone, and unsupported or
        ambiguous claims are kept as separate fields so a claim is never
        presented as an established result.

    Raises
    ------
    ValueError
        When two records share an organisation name.
    """
    companies: list[dict[str, Any]] = []
    audited_companies = (
        {row["company"]: row for row in read_tsv(COMPANY_AUDIT_SOURCE)}
        if COMPANY_AUDIT_SOURCE.exists()
        else {}
    )
    for row in read_tsv(COMPANY_SOURCE):
        audit = audited_companies.get(row["company"])
        if audit:
            detail_status = audit["normalized_status"]
            status_key = detail_status.lower()
            if status_key.startswith("active"):
                display_status = "active"
            elif any(
                token in status_key
                for token in ("closed", "acquired", "dormant", "historical", "no current")
            ):
                display_status = "historical / inactive / unclear"
            else:
                display_status = "status uncertain"
            independent_urls = [
                url.strip() for url in audit["independent_urls"].split(";") if url.strip()
            ]
            source_urls = list(
                dict.fromkeys(
                    ([audit["official_url"]] if audit["official_url"] else []) + independent_urls
                )
            )
            companies.append(
                {
                    **row,
                    **audit,
                    "name": row["company"],
                    "status": display_status,
                    "status_detail": detail_status,
                    "approach": audit["approach_family"],
                    "evidence": audit["evidence_tier"].split(" — ", 1)[0],
                    "company_claim": audit["company_claim_summary"],
                    "independent_evidence": audit["highest_independently_supported_milestone"],
                    "source_url": source_urls[0],
                    "source_urls": source_urls,
                    "source_checked": audit["audit_date"],
                    "dataset_source": "metadata/company_audit/audited_companies.tsv",
                    "data_caveat": audit["unsupported_or_ambiguous_claims"],
                }
            )
            continue
        companies.append(
            {
                **row,
                "name": row["company"],
                "status": row["active_status"],
                "evidence": "unassessed",
                "company_claim": row["claimed_milestones"],
                "independent_evidence": "Candidate catalog assessment (not re-audited here): "
                + row["evidence_maturity"],
                "source_url": row["official_url"] or row["independent_source_url"],
                "source_checked": row["last_verified"],
                "dataset_source": "metadata/discovery_audit/fusion_companies_candidates.tsv",
                "data_caveat": "Discovery candidate, not independently verified company status or reactor performance. Independent-source links may provide sector context rather than company-specific corroboration.",
            }
        )
    expansion_sources = (
        (COMPANY_EXPANSION_SOURCE, "official_url"),
        (COMPANY_EXPANSION_ROUND2_SOURCE, "primary_url"),
        (COMPANY_EXPANSION_ROUND3_SOURCE, "primary_url"),
    )
    for expansion_source, primary_url_field in expansion_sources:
        if not expansion_source.exists():
            continue
        for row in read_tsv(expansion_source):
            detail_status = row["normalized_status"]
            status_key = detail_status.lower()
            if status_key.startswith("active"):
                display_status = "active"
            elif any(token in status_key for token in ("dormant", "inactive", "historical")):
                display_status = "historical / inactive / unclear"
            else:
                display_status = "status uncertain"
            independent_urls = [
                url.strip() for url in row["independent_urls"].split(";") if url.strip()
            ]
            source_urls = list(
                dict.fromkeys(url for url in [row[primary_url_field], *independent_urls] if url)
            )
            companies.append(
                {
                    **row,
                    "name": row["organization"],
                    "status": display_status,
                    "status_detail": detail_status,
                    "approach": row["approach_family"],
                    "evidence": row["evidence_tier"].split(" — ", 1)[0],
                    "company_claim": row["company_claim_summary"],
                    "independent_evidence": row["highest_independently_supported_milestone"],
                    "source_url": source_urls[0],
                    "source_urls": source_urls,
                    "source_checked": row["audit_date"],
                    "dataset_source": str(expansion_source.relative_to(LIBRARY)),
                    "data_caveat": row["unsupported_or_ambiguous_claims"],
                }
            )
    companies_by_name: dict[str, dict[str, Any]] = {row["name"]: row for row in companies}
    if COMPANY_DEPTH_MATRIX_SOURCE.exists():
        for depth_row in read_tsv(COMPANY_DEPTH_MATRIX_SOURCE):
            target = companies_by_name[depth_row["organization"]]
            if depth_row["fuel_cycle_completeness"] == "complete" and depth_row["fuel_cycle"]:
                target["fuel_cycle"] = depth_row["fuel_cycle"]
    for depth_source in (
        COMPANY_DEPTH_OVERLAY_SOURCE,
        COMPANY_DEPTH_ROUND5_SOURCE,
        COMPANY_DEPTH_ROUND6_SOURCE,
        COMPANY_DEPTH_ROUND7_SOURCE,
        COMPANY_DEPTH_ROUND8_SOURCE,
    ):
        if not depth_source.exists():
            continue
        for overlay in read_tsv(depth_source):
            target = companies_by_name[overlay["organization"]]
            independent_urls = [
                url.strip()
                for url in overlay["enriched_independent_urls"].split(";")
                if url.strip()
            ]
            source_urls = list(
                dict.fromkeys(
                    [
                        overlay["enriched_official_url"] or target["source_url"],
                        *independent_urls,
                    ]
                )
            )
            status_detail = overlay["enriched_status"] or target.get(
                "status_detail", target["status"]
            )
            target.update(
                {
                    "identity_class": overlay.get("enriched_identity_class")
                    or target.get("identity_class", ""),
                    "status_detail": status_detail,
                    "status": "active"
                    if status_detail.lower().startswith("active")
                    else target["status"],
                    "country": overlay.get("enriched_country") or target["country"],
                    "approach": overlay["enriched_approach_configuration"]
                    or target.get("approach", ""),
                    "approach_family": overlay["enriched_approach_configuration"]
                    or target.get("approach_family", ""),
                    "public_devices_projects": overlay["enriched_named_devices_projects"]
                    or target.get("public_devices_projects", ""),
                    "fuel_cycle": overlay["enriched_fuel_cycle"],
                    "independent_evidence": overlay[
                        "enriched_highest_independently_supported_milestone"
                    ]
                    or target["independent_evidence"],
                    "data_caveat": overlay["enriched_unsupported_or_ambiguous_claims"]
                    or target["data_caveat"],
                    "source_url": overlay["enriched_official_url"] or source_urls[0],
                    "source_urls": source_urls,
                    "source_checked": overlay["audit_date"],
                    "confidence": overlay["confidence"] or target.get("confidence", ""),
                    "depth_enrichment_applied": True,
                    "depth_enrichment_source": str(depth_source.relative_to(LIBRARY)),
                }
            )
            for field, display_field in (
                ("normalized_status", "status_detail"),
                ("highest_independently_supported_milestone", "independent_evidence"),
                ("unsupported_or_ambiguous_claims", "data_caveat"),
                ("official_url", "source_url"),
                ("audit_date", "source_checked"),
            ):
                target[field] = target[display_field]
            target["source_dates"] = overlay["source_dates"]
            target["independent_urls"] = overlay["enriched_independent_urls"]
    if len({r["name"] for r in companies}) != len(companies):
        raise ValueError("Duplicate company name")
    return companies


def normalise_facility_countries(facilities: list[dict[str, Any]]) -> None:
    """Collapse country aliases for filtering, preserving the source value.

    The original source spelling is retained as ``source_country`` whenever
    it differs, so normalising for the user interface never destroys what
    the publisher actually recorded.

    Parameters
    ----------
    facilities : list of dict
        The assembled facility records, modified in place.
    """
    for row in facilities:
        source_country = row.get("country") or ""
        normalized_country = normalize_country(source_country)
        if normalized_country != source_country:
            row["source_country"] = source_country
            row["country"] = normalized_country


def require_source_urls(facilities: list[dict[str, Any]], companies: list[dict[str, Any]]) -> None:
    """Refuse to publish a record that cannot be traced to a source.

    Parameters
    ----------
    facilities : list of dict
        The assembled facility records.
    companies : list of dict
        The assembled company records.

    Raises
    ------
    ValueError
        When any record lacks an HTTP or HTTPS source URL.
    """
    if not all(r["source_url"].startswith(("http://", "https://")) for r in facilities + companies):
        raise ValueError("every record must carry an HTTP(S) source URL")


def merge_supplemental_context(facilities: list[dict[str, Any]]) -> int:
    """Fold supplemental context records into matching facility records.

    A supplemental record adds context to a facility already discovered by
    a registry; it merges by exact name and domain, so it can never invent
    a facility the registries did not supply.

    Parameters
    ----------
    facilities : list of dict
        The assembled facility records, modified in place.

    Returns
    -------
    int
        How many supplemental records merged into an existing facility.
    """
    merged_supplemental = 0
    supplemental_rows = [
        row
        for row in facilities
        if row.get("dataset_source")
        == "04_interactive_presentation/data/facilities-supplemental.json"
    ]
    for supplemental in supplemental_rows:
        matches = [
            row
            for row in facilities
            if row is not supplemental
            and row.get("domain") == supplemental.get("domain")
            and row.get("dataset_source") != f"{FFDB_INTEGRATION.LAYER}/fusion_facilities.tsv"
            and str(row.get("name") or "").casefold().strip()
            == str(supplemental.get("name") or "").casefold().strip()
        ]
        if len(matches) != 1:
            continue
        target = matches[0]
        if target.get("lat") is None and supplemental.get("lat") is not None:
            target["lat"], target["lon"] = supplemental["lat"], supplemental["lon"]
            target["completeness"] = "partial"
            target["data_caveat"] += (
                " Approximate coordinates were retained from the original presentation record."
            )
        target["source_urls"] = list(
            dict.fromkeys(
                (target.get("source_urls") or [target["source_url"]]) + [supplemental["source_url"]]
            )
        )
        facilities.remove(supplemental)
        merged_supplemental += 1
    return merged_supplemental


def write_dataset_manifest(
    facilities: list[dict[str, Any]],
    companies: list[dict[str, Any]],
    merged_supplemental: int,
    fusion_source: str,
    fusion_records: int,
) -> None:
    """Record which inputs produced this build, and their digests.

    The manifest is what lets a reader establish that a published dataset
    came from a particular set of source files, rather than taking the
    counts on trust. All seven round-seven bundle artifacts are individually
    hashed; supplemental counts refer to records rather than wrapper keys.

    Parameters
    ----------
    facilities : list of dict
        The assembled facility records.
    companies : list of dict
        The assembled company records.
    merged_supplemental : int
        How many supplemental records merged into an existing facility.
    fusion_source : str
        Explicit source selection: pinned FFDB or the historical import.
    fusion_records : int
        Source rows used from the selected primary fusion catalogue.
    """
    input_paths = [FACILITY_SOURCE, COMPANY_SOURCE, SUPPLEMENT]
    input_paths.extend(LIBRARY / member for member in FIELD_MEMBERS if (LIBRARY / member).exists())
    if INDUSTRIAL_ROUND7_SOURCE.exists():
        input_paths.extend(
            INDUSTRIAL_ROUND7_SOURCE.parent / name
            for name in INDUSTRIAL_ROUND7_VALIDATOR.BUNDLE_FILES
            if name != INDUSTRIAL_ROUND7_SOURCE.name
        )
    if COMPANY_AUDIT_SOURCE.exists():
        input_paths.append(COMPANY_AUDIT_SOURCE)
    if COMPANY_EXPANSION_SOURCE.exists():
        input_paths.append(COMPANY_EXPANSION_SOURCE)
    if COMPANY_EXPANSION_ROUND2_SOURCE.exists():
        input_paths.append(COMPANY_EXPANSION_ROUND2_SOURCE)
    if COMPANY_EXPANSION_ROUND3_SOURCE.exists():
        input_paths.append(COMPANY_EXPANSION_ROUND3_SOURCE)
    if COMPANY_DEPTH_OVERLAY_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_OVERLAY_SOURCE)
    if COMPANY_DEPTH_MATRIX_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_MATRIX_SOURCE)
    if COMPANY_DEPTH_ROUND5_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_ROUND5_SOURCE)
    if COMPANY_DEPTH_ROUND6_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_ROUND6_SOURCE)
    if COMPANY_DEPTH_ROUND7_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_ROUND7_SOURCE)
    if COMPANY_DEPTH_ROUND8_SOURCE.exists():
        input_paths.append(COMPANY_DEPTH_ROUND8_SOURCE)
    input_paths.extend(
        path
        for path in (
            RESEARCH_SOURCE,
            POWER_UNIT_SOURCE,
            INDUSTRIAL_SOURCE,
            INDUSTRIAL_ROUND2_SOURCE,
            INDUSTRIAL_ROUND3_SOURCE,
            INDUSTRIAL_ROUND4_SOURCE,
            INDUSTRIAL_ROUND5_SOURCE,
            INDUSTRIAL_ROUND6_SOURCE,
            INDUSTRIAL_ROUND7_SOURCE,
        )
        if path.exists()
    )
    if fusion_source == "ffdb":
        input_paths.extend(LIBRARY / member for member in FFDB_INTEGRATION.INPUTS)
    else:
        input_paths.extend(
            path
            for path in (
                FUSION_SOURCE,
                FUSION_ENRICHMENT_SOURCE,
                FUSION_ENRICHMENT_ROUND2_SOURCE,
                FUSION_ENRICHMENT_ROUND3_SOURCE,
                FUSION_NEW_SOURCE,
            )
            if path.exists()
        )
    if RESEARCH_ENRICHMENT_SOURCE.exists():
        input_paths.append(RESEARCH_ENRICHMENT_SOURCE)
    if RESEARCH_ENRICHMENT_ROUND2_SOURCE.exists():
        input_paths.append(RESEARCH_ENRICHMENT_ROUND2_SOURCE)
    if RESEARCH_ENRICHMENT_ROUND3_SOURCE.exists():
        input_paths.append(RESEARCH_ENRICHMENT_ROUND3_SOURCE)
    if RESEARCH_ENRICHMENT_ROUND4_SOURCE.exists():
        input_paths.append(RESEARCH_ENRICHMENT_ROUND4_SOURCE)
    if RESEARCH_ENRICHMENT_ROUND5_SOURCE.exists():
        input_paths.append(RESEARCH_ENRICHMENT_ROUND5_SOURCE)
    if FUSION_SNAPSHOT is not None:
        input_paths.extend(FUSION_SNAPSHOT / member for member in HISTORICAL_INPUTS.MEMBERS)
    input_paths.extend(
        RESEARCH_SOURCE.parent / "official_source_enrichment" / member
        for member in PRIMARY_RESEARCH.MEMBERS
        if (RESEARCH_SOURCE.parent / "official_source_enrichment" / member).exists()
    )
    inventory = {
        "research_primary_decisions": {
            decision: sum(
                assertion["selection"] == decision
                for record in facilities
                for assertion in record.get("research_primary_assertions", [])
            )
            for decision in (
                "selected",
                "held",
                "unknown",
                "not_applicable",
                "never_critical",
                "planned",
                "composite",
            )
        },
        "facilities": len(facilities),
        "imported_plant_records": len(read_tsv(FACILITY_SOURCE)),
        "supplemental_facilities": len(
            _records_of(json.loads(SUPPLEMENT.read_text(encoding="utf-8")))
        ),
        "merged_supplemental_duplicates": merged_supplemental,
        "fusion_source": fusion_source,
        "imported_fusion_facilities": fusion_records,
        "fusion_facility_enrichments": len(read_tsv(FUSION_ENRICHMENT_SOURCE))
        if fusion_source.startswith("historical") and FUSION_ENRICHMENT_SOURCE.exists()
        else 0,
        "fusion_facility_enrichments_round2": len(read_tsv(FUSION_ENRICHMENT_ROUND2_SOURCE))
        if fusion_source.startswith("historical") and FUSION_ENRICHMENT_ROUND2_SOURCE.exists()
        else 0,
        "fusion_facility_enrichments_round3": len(read_tsv(FUSION_ENRICHMENT_ROUND3_SOURCE))
        if fusion_source.startswith("historical") and FUSION_ENRICHMENT_ROUND3_SOURCE.exists()
        else 0,
        "new_fusion_facilities": len(read_tsv(FUSION_NEW_SOURCE))
        if fusion_source.startswith("historical") and FUSION_NEW_SOURCE.exists()
        else 0,
        "imported_research_reactors": len(read_tsv(RESEARCH_SOURCE))
        if RESEARCH_SOURCE.exists()
        else 0,
        "research_reactor_enrichments": len(read_tsv(RESEARCH_ENRICHMENT_SOURCE))
        if RESEARCH_ENRICHMENT_SOURCE.exists()
        else 0,
        "research_reactor_enrichments_round2": len(read_tsv(RESEARCH_ENRICHMENT_ROUND2_SOURCE))
        if RESEARCH_ENRICHMENT_ROUND2_SOURCE.exists()
        else 0,
        "research_reactor_enrichments_round3": len(read_tsv(RESEARCH_ENRICHMENT_ROUND3_SOURCE))
        if RESEARCH_ENRICHMENT_ROUND3_SOURCE.exists()
        else 0,
        "research_reactor_enrichments_round4": len(read_tsv(RESEARCH_ENRICHMENT_ROUND4_SOURCE))
        if RESEARCH_ENRICHMENT_ROUND4_SOURCE.exists()
        else 0,
        "research_reactor_enrichments_round5": len(read_tsv(RESEARCH_ENRICHMENT_ROUND5_SOURCE))
        if RESEARCH_ENRICHMENT_ROUND5_SOURCE.exists()
        else 0,
        "imported_power_reactor_units": len(read_tsv(POWER_UNIT_SOURCE))
        if POWER_UNIT_SOURCE.exists()
        else 0,
        "imported_industrial_facilities": len(read_tsv(INDUSTRIAL_SOURCE))
        if INDUSTRIAL_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round2": len(read_tsv(INDUSTRIAL_ROUND2_SOURCE))
        if INDUSTRIAL_ROUND2_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round3": len(read_tsv(INDUSTRIAL_ROUND3_SOURCE))
        if INDUSTRIAL_ROUND3_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round4": len(read_tsv(INDUSTRIAL_ROUND4_SOURCE))
        if INDUSTRIAL_ROUND4_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round5": len(read_tsv(INDUSTRIAL_ROUND5_SOURCE))
        if INDUSTRIAL_ROUND5_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round6": len(read_tsv(INDUSTRIAL_ROUND6_SOURCE))
        if INDUSTRIAL_ROUND6_SOURCE.exists()
        else 0,
        "imported_industrial_facilities_round7": len(read_tsv(INDUSTRIAL_ROUND7_SOURCE))
        if INDUSTRIAL_ROUND7_SOURCE.exists()
        else 0,
        "companies_and_programs": len(companies),
        "company_expansion_records": len(read_tsv(COMPANY_EXPANSION_SOURCE))
        if COMPANY_EXPANSION_SOURCE.exists()
        else 0,
        "company_expansion_round2_records": len(read_tsv(COMPANY_EXPANSION_ROUND2_SOURCE))
        if COMPANY_EXPANSION_ROUND2_SOURCE.exists()
        else 0,
        "company_expansion_round3_records": len(read_tsv(COMPANY_EXPANSION_ROUND3_SOURCE))
        if COMPANY_EXPANSION_ROUND3_SOURCE.exists()
        else 0,
        "company_depth_enrichments": len(read_tsv(COMPANY_DEPTH_OVERLAY_SOURCE))
        if COMPANY_DEPTH_OVERLAY_SOURCE.exists()
        else 0,
        "company_depth_matrix_records": len(read_tsv(COMPANY_DEPTH_MATRIX_SOURCE))
        if COMPANY_DEPTH_MATRIX_SOURCE.exists()
        else 0,
        "company_depth_round5_enrichments": len(read_tsv(COMPANY_DEPTH_ROUND5_SOURCE))
        if COMPANY_DEPTH_ROUND5_SOURCE.exists()
        else 0,
        "company_depth_round6_enrichments": len(read_tsv(COMPANY_DEPTH_ROUND6_SOURCE))
        if COMPANY_DEPTH_ROUND6_SOURCE.exists()
        else 0,
        "company_depth_round7_enrichments": len(read_tsv(COMPANY_DEPTH_ROUND7_SOURCE))
        if COMPANY_DEPTH_ROUND7_SOURCE.exists()
        else 0,
        "company_depth_round8_enrichments": len(read_tsv(COMPANY_DEPTH_ROUND8_SOURCE))
        if COMPANY_DEPTH_ROUND8_SOURCE.exists()
        else 0,
        "facility_field_assertions": sum(
            len(row.get("field_observations", [])) for row in facilities
        ),
        "facility_domains": dict(Counter(row["domain"] for row in facilities)),
        "facility_statuses": dict(Counter(row["status"] for row in facilities)),
        "inputs": {
            _relative_label(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in input_paths
        },
    }
    (DATA / "dataset-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(inventory, indent=2))


def main(argv: list[str] | None = None) -> None:
    """Build every integrated dataset the atlas loads.

    Parameters
    ----------
    argv : list of str or None
        Command-line arguments. ``--source-root`` and ``--data-dir`` let a
        caller build from a different tree, which is how the tests exercise
        this script as a real process. ``--fusion-source`` selects pinned FFDB
        by default; ``historical`` selects the attributed subset, optionally
        from an explicit verified bundle, and
        ``historical-full`` requires an explicit immutable historical bundle.
    """
    parser = argparse.ArgumentParser(description="Build the integrated atlas datasets.")
    parser.add_argument("--source-root", type=Path, default=LIBRARY)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument(
        "--fusion-source", choices=("ffdb", "historical", "historical-full"), default="ffdb"
    )
    parser.add_argument("--historical-bundle", type=Path)
    arguments = parser.parse_args(argv)
    if arguments.fusion_source == "historical-full" and arguments.historical_bundle is None:
        parser.error("historical-full requires --historical-bundle with exact frozen inputs")
    if arguments.historical_bundle is not None and arguments.fusion_source == "ffdb":
        parser.error("--historical-bundle requires --fusion-source historical or historical-full")
    configure_roots(arguments.source_root, arguments.data_dir)
    with tempfile.TemporaryDirectory(prefix="atlas-historical-") as workspace:
        if arguments.historical_bundle is not None:
            source = arguments.historical_bundle
            try:
                HISTORICAL_INPUTS.materialize(
                    source,
                    Path(workspace),
                    selection="frozen"
                    if arguments.fusion_source == "historical-full"
                    else "public",
                )
            except HISTORICAL_INPUTS.HistoricalInputRefusal as error:
                parser.exit(2, f"Historical inputs refused: {error}\n")
            except (OSError, UnicodeError, csv.Error, ValueError):
                parser.exit(
                    2,
                    "Historical inputs refused: source inputs or snapshot output are invalid or unavailable\n",
                )
            configure_historical_snapshot(Path(workspace))
        if arguments.fusion_source == "ffdb":
            fusion_facilities = FFDB_INTEGRATION.build_facilities(LIBRARY, normalize_status)
            fusion_records = len(fusion_facilities)
        else:
            fusion_facilities = build_fusion_facilities(
                FUSION_SOURCE,
                (
                    FUSION_ENRICHMENT_SOURCE,
                    FUSION_ENRICHMENT_ROUND2_SOURCE,
                    FUSION_ENRICHMENT_ROUND3_SOURCE,
                ),
                FUSION_NEW_SOURCE,
            )
            fusion_records = len(read_tsv(FUSION_SOURCE)) if FUSION_SOURCE.exists() else 0
        try:
            research_facilities = build_research_facilities(
                RESEARCH_SOURCE,
                (
                    RESEARCH_ENRICHMENT_SOURCE,
                    RESEARCH_ENRICHMENT_ROUND2_SOURCE,
                    RESEARCH_ENRICHMENT_ROUND3_SOURCE,
                    RESEARCH_ENRICHMENT_ROUND4_SOURCE,
                    RESEARCH_ENRICHMENT_ROUND5_SOURCE,
                ),
            )
        except (OSError, UnicodeError, csv.Error, ValueError):
            parser.exit(
                2,
                "Primary research inputs refused; check original sources and complete field review.\n",
            )
        arguments.data_dir.mkdir(parents=True, exist_ok=True)
        facilities: list[dict[str, Any]] = build_base_facilities(FACILITY_SOURCE)
        facilities.extend(fusion_facilities)
        facilities.extend(research_facilities)
        facilities.extend(build_power_unit_facilities(POWER_UNIT_SOURCE))
        facilities.extend(
            build_industrial_facilities(
                (
                    INDUSTRIAL_SOURCE,
                    INDUSTRIAL_ROUND2_SOURCE,
                    INDUSTRIAL_ROUND3_SOURCE,
                    INDUSTRIAL_ROUND4_SOURCE,
                    INDUSTRIAL_ROUND5_SOURCE,
                    INDUSTRIAL_ROUND6_SOURCE,
                    INDUSTRIAL_ROUND7_SOURCE,
                )
            )
        )
        merged_supplemental = merge_supplemental_context(facilities)
        if len({r["id"] for r in facilities}) != len(facilities):
            raise ValueError("Duplicate facility ID")

        companies: list[dict[str, Any]] = build_companies()
        normalise_facility_countries(facilities)
        require_source_urls(facilities, companies)
        apply_fields(LIBRARY, facilities)
        emit(
            "global_reactors.sample",
            "REACTOR_FACILITIES",
            facilities,
            schema_version="1.3.0"
            if any(row.get("research_primary_assertions") for row in facilities)
            else "1.2.0",
        )
        emit("fusion_companies.sample", "FUSION_COMPANIES", companies)
        write_dataset_manifest(
            facilities, companies, merged_supplemental, arguments.fusion_source, fusion_records
        )


if __name__ == "__main__":
    main()
