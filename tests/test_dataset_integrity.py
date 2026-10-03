# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_dataset_integrity.py

"""Invariants the published datasets must satisfy.

These run against the shipped data rather than a fixture, so a regression in
any builder, enrichment round or overlay surfaces here regardless of which
script introduced it.
"""

from __future__ import annotations

from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

EXPECTED_FACILITIES = 13459
EXPECTED_MAPPED = 13357
EXPECTED_COMPANIES = 98
EXPECTED_DOMAINS = {"fission": 2192, "fusion": 180, "chemical": 11086, "hybrid": 1}


def has_coordinates(record: dict[str, Any]) -> bool:
    """Report whether a record carries a usable coordinate pair."""
    lat, lon = record.get("lat"), record.get("lon")
    return lat not in (None, "") and lon not in (None, "")


class TestPublishedCounts:
    """The snapshot the atlas advertises must be the snapshot it ships."""

    def test_facility_count(self, facilities: list[dict[str, Any]]) -> None:
        assert len(facilities) == EXPECTED_FACILITIES

    def test_mapped_count(self, facilities: list[dict[str, Any]]) -> None:
        assert sum(1 for r in facilities if has_coordinates(r)) == EXPECTED_MAPPED

    def test_company_count(self, companies: list[dict[str, Any]]) -> None:
        assert len(companies) == EXPECTED_COMPANIES

    def test_domain_breakdown(self, facilities: list[dict[str, Any]]) -> None:
        counts: dict[str, int] = {}
        for record in facilities:
            counts[record["domain"]] = counts.get(record["domain"], 0) + 1
        assert counts == EXPECTED_DOMAINS


class TestIdentity:
    """Records must be individually addressable."""

    def test_facility_ids_are_unique(self, facilities: list[dict[str, Any]]) -> None:
        ids = [r["id"] for r in facilities]
        assert len(set(ids)) == len(ids)

    def test_company_names_are_unique(self, companies: list[dict[str, Any]]) -> None:
        names = [r["name"] for r in companies]
        assert len(set(names)) == len(names)

    def test_every_facility_id_is_url_and_dom_safe(self, facilities: list[dict[str, Any]]) -> None:
        import re

        bad = [r["id"] for r in facilities if not re.fullmatch(r"[a-z0-9:._-]+", r["id"])]
        assert bad == [], f"unsafe identifiers: {bad[:5]}"


class TestCoordinates:
    """A coordinate must be real, or absent — never invented."""

    def test_all_coordinates_are_in_range(self, facilities: list[dict[str, Any]]) -> None:
        out_of_range = [
            r["id"]
            for r in facilities
            if has_coordinates(r)
            and not (-90 <= float(r["lat"]) <= 90 and -180 <= float(r["lon"]) <= 180)
        ]
        assert out_of_range == []

    def test_no_record_sits_at_null_island(self, facilities: list[dict[str, Any]]) -> None:
        # 0,0 is in the Gulf of Guinea and is the classic signature of a
        # missing coordinate silently coerced to zero.
        at_origin = [
            r["id"]
            for r in facilities
            if has_coordinates(r) and float(r["lat"]) == 0.0 and float(r["lon"]) == 0.0
        ]
        assert at_origin == []

    def test_unmapped_records_have_no_partial_coordinate(
        self, facilities: list[dict[str, Any]]
    ) -> None:
        # A record with a latitude but no longitude would be plotted wrongly
        # or dropped inconsistently depending on the consumer.
        partial = [
            r["id"]
            for r in facilities
            if (r.get("lat") not in (None, "")) != (r.get("lon") not in (None, ""))
        ]
        assert partial == []


class TestProvenance:
    """Every record must be traceable to a source."""

    def test_every_facility_has_an_http_source_url(self, facilities: list[dict[str, Any]]) -> None:
        missing = [
            r["id"]
            for r in facilities
            if not str(r.get("source_url", "")).startswith(("http://", "https://"))
        ]
        assert missing == []

    def test_every_company_has_an_http_source_url(self, companies: list[dict[str, Any]]) -> None:
        missing = [
            r["name"]
            for r in companies
            if not str(r.get("source_url", "")).startswith(("http://", "https://"))
        ]
        assert missing == []

    def test_every_facility_declares_a_dataset_source(
        self, facilities: list[dict[str, Any]]
    ) -> None:
        missing = [r["id"] for r in facilities if not str(r.get("dataset_source", "")).strip()]
        assert missing == []

    def test_every_facility_carries_a_data_caveat(self, facilities: list[dict[str, Any]]) -> None:
        # The atlas's central claim is that a record is a source row, not a
        # verified reactor vessel; the caveat is how that reaches the reader.
        missing = [r["id"] for r in facilities if not str(r.get("data_caveat", "")).strip()]
        assert missing == []


class TestSchemaConformance:
    """The shipped data must validate against the shipped schema."""

    def test_facilities_match_their_schema(
        self, facilities: list[dict[str, Any]], facility_schema: dict[str, Any]
    ) -> None:
        # The schema describes the whole document, wrapper included.
        document = {
            "schema_version": "1.1.0",
            "record_count": len(facilities),
            "records": facilities,
        }
        validator = Draft202012Validator(facility_schema, format_checker=FormatChecker())
        errors = list(validator.iter_errors(document))
        assert errors == [], (
            f"{len(errors)} schema errors; first: {errors[0].message if errors else ''}"
        )

    def test_companies_match_their_schema(
        self, companies: list[dict[str, Any]], company_schema: dict[str, Any]
    ) -> None:
        document = {
            "schema_version": "1.0.0",
            "record_count": len(companies),
            "records": companies,
        }
        validator = Draft202012Validator(company_schema, format_checker=FormatChecker())
        errors = list(validator.iter_errors(document))
        assert errors == [], (
            f"{len(errors)} schema errors; first: {errors[0].message if errors else ''}"
        )


class TestEvidenceDiscipline:
    """Claims and evidence must stay separable."""

    @pytest.mark.parametrize("field", ["domain", "status", "evidence"])
    def test_classification_fields_are_always_populated(
        self, facilities: list[dict[str, Any]], field: str
    ) -> None:
        missing = [r["id"] for r in facilities if not str(r.get(field, "")).strip()]
        assert missing == []

    def test_status_values_are_lower_case_normalised(
        self, facilities: list[dict[str, Any]]
    ) -> None:
        odd = {r["status"] for r in facilities if r["status"] != r["status"].lower()}
        assert odd == set()

    def test_no_status_is_blank(self, facilities: list[dict[str, Any]]) -> None:
        # A blank status would be indistinguishable from "operational" in a
        # filter; absence must read as "unknown".
        assert [r["id"] for r in facilities if r["status"] == ""] == []
