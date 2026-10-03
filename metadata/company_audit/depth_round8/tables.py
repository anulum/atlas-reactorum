#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round8/tables.py
"""Ordered TSV contracts and verbatim row loading for company-depth8 metadata."""

from __future__ import annotations

import csv
from pathlib import Path

PROFILE_FIELDS = "organization match_rule source_record_id fields_enriched enriched_status enriched_approach_configuration enriched_named_devices_projects enriched_fuel_cycle enriched_highest_independently_supported_milestone enriched_unsupported_or_ambiguous_claims enriched_official_url enriched_independent_urls source_ids source_dates audit_date confidence overlay_note".split()
SOURCE_FIELDS = "source_id organization title publisher source_type source_date url scope_and_limitations accessed_on".split()
BINDING_FIELDS = "organization field source_ids interpretation reviewed_on".split()
MATRIX_FIELDS = "record_id source_catalog source_row organization country identity_class normalized_status approach_configuration named_devices_projects fuel_cycle highest_independently_supported_milestone unsupported_or_ambiguous_claims official_url independent_sources source_dates confidence evidence_tier status_completeness identity_completeness approach_completeness device_completeness fuel_cycle_completeness milestone_completeness unsupported_claims_completeness official_url_completeness independent_source_completeness source_date_completeness country_completeness confidence_completeness gap_count priority_score priority_band gap_fields".split()
EARLY_FIELDS = "organization match_rule source_record_id fields_enriched enriched_identity_class enriched_status enriched_country enriched_approach_configuration enriched_named_devices_projects enriched_fuel_cycle enriched_highest_independently_supported_milestone enriched_unsupported_or_ambiguous_claims enriched_official_url enriched_independent_urls source_ids source_dates audit_date confidence overlay_note".split()


def read_table(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a complete TSV using its exact ordered schema.

    Parameters
    ----------
    path : pathlib.Path
        Real source or persisted product to inspect without rewriting.
    fields : list of str
        Ordered producer contract.

    Returns
    -------
    list of dict
        Verbatim cell text, including legitimate historical missing values.

    Raises
    ------
    ValueError
        The header, row shape or record count is invalid.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", strict=True)
        if next(reader, []) != fields:
            raise ValueError(f"{path.name}: unexpected header")
        records = list(reader)
    if not records or any(len(row) != len(fields) for row in records):
        raise ValueError(f"{path.name}: empty or malformed table")
    return [dict(zip(fields, row, strict=True)) for row in records]
