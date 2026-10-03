# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/_source_shape.py

"""The facility source schema, read from the real catalogue.

Tests build synthetic rows with the same columns the production source
uses, so a schema change breaks the tests rather than letting them pass
against a shape the builder no longer accepts.
"""

from __future__ import annotations

FACILITY_COLUMNS: list[str] = [
    "id",
    "name",
    "aliases",
    "record_kind",
    "domain",
    "reactor_type",
    "subtypes",
    "purpose",
    "status",
    "evidence_maturity",
    "site",
    "city",
    "region",
    "country",
    "country_code",
    "latitude",
    "longitude",
    "coordinate_precision",
    "coordinate_source",
    "owner",
    "operator",
    "designer",
    "regulator",
    "fuel_or_feed",
    "coolant_or_medium",
    "moderator",
    "confinement_or_flow",
    "thermal_power_mw",
    "electric_power_mw",
    "capacity_note",
    "start_date",
    "end_date",
    "source_url",
    "source_publisher",
    "source_title",
    "source_role",
    "source_license",
    "source_quality_flags",
    "last_verified",
    "verification_notes",
]

COMPANY_COLUMNS: list[str] = [
    "company",
    "aliases",
    "country",
    "founded",
    "active_status",
    "approach",
    "devices/projects",
    "claimed_milestones",
    "evidence_maturity",
    "publications_or_patents",
    "official_url",
    "independent_source_url",
    "registry_sources",
    "last_verified",
]

COMPANY_SAMPLE_ROW: dict[str, str] = {
    "company": "Commonwealth Fusion Systems",
    "aliases": "CFS",
    "country": "United States",
    "founded": "2018",
    "active_status": "active",
    "approach": "high-field compact tokamak; D-T; HTS magnets",
    "devices/projects": "SPARC; ARC",
    "claimed_milestones": "SPARC construction and ARC commercial plant plans; company schedules are claims",
    "evidence_maturity": "major hardware tested; integrated device under construction; no fusion-electricity demonstration",
    "publications_or_patents": "Peer-reviewed SPARC physics and HTS magnet papers",
    "official_url": "https://cfs.energy/",
    "independent_source_url": "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine",
    "registry_sources": "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf; IAEA FUSDIS; DOE Milestone Program",
    "last_verified": "2026-09-26",
}

FUSION_COLUMNS: list[str] = [
    "stable_id",
    "name",
    "aliases",
    "country",
    "latitude",
    "longitude",
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
    "verification_evidence_notes",
]

FUSION_SAMPLE_ROW: dict[str, str] = {
    "stable_id": "fusionbenchmark:aditya-u",
    "name": "ADITYA-U",
    "aliases": "",
    "country": "India",
    "latitude": "",
    "longitude": "",
    "coordinate_precision": "",
    "configuration": "magnetic confinement",
    "device_subtype": "Tokamak",
    "status": "Operating",
    "organization": "Institute for Plasma Research",
    "first_operation_date": "",
    "last_operation_date": "",
    "source_url": "https://www-pub.iaea.org/MTCD/Publications/PDF/CRCP-FUS-001webRev.pdf | https://fusionbenchmark.com/facility/aditya-u/",
    "source_role": "independent | licensed aggregator",
    "retrieved_date": "2026-09-26",
    "license": "CC BY 4.0 (FusionBenchmark compilation); CC0 1.0 (Wikidata fields where cited)",
    "verification_evidence_notes": "Name, operator, type, approach, country and status transcribed from the cited FusionBenchmark device record. No unique exact Wikidata label match; coordinates, aliases and operation dates left unknown rather than inferred.",
}

RESEARCH_COLUMNS: list[str] = [
    "stable_id",
    "name",
    "aliases",
    "country",
    "lat",
    "lon",
    "precision",
    "reactor_type",
    "status",
    "purpose",
    "thermal_power_mw",
    "operator",
    "first_criticality",
    "shutdown_date",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]

RESEARCH_SAMPLE_ROW: dict[str, str] = {
    "stable_id": "wikidata-q116044260",
    "name": "ALFRED",
    "aliases": "",
    "country": "",
    "lat": "",
    "lon": "",
    "precision": "unknown",
    "reactor_type": "research reactor",
    "status": "unknown",
    "purpose": "",
    "thermal_power_mw": "",
    "operator": "",
    "first_criticality": "",
    "shutdown_date": "",
    "source_url": "https://www.wikidata.org/wiki/Q116044260",
    "source_role": "open discovery registry",
    "retrieved": "2026-09-26",
    "license": "CC0 1.0",
    "verification_notes": "CC0 Wikidata discovery record; community-edited and not authoritative. Coordinates, type, dates, and status require verification against a regulator, operator, or IAEA RRDB. First criticality and thermal power are blank unless an unambiguous reusable source supplies those exact concepts. No coordinate assertion was available in the retrieved Wikidata entity.",
}
