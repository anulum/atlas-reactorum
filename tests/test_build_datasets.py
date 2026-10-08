# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_build_datasets.py

"""Tests for the dataset builder's normalisation and emission behaviour."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest


class TestNullableNumber:
    """An absent measurement must stay absent, never become zero."""

    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_absent_values_yield_none(self, build_datasets: ModuleType, value: str | None) -> None:
        """Missing and whitespace-only measurements remain None rather than becoming a numeric zero."""
        assert build_datasets.nullable_number(value) is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("0.0", 0.0),
            ("375", 375.0),
            ("-12.5", -12.5),
            ("  42  ", 42.0),
            ("1e3", 1000.0),
        ],
    )
    def test_numbers_parse(self, build_datasets: ModuleType, value: str, expected: float) -> None:
        """Explicit decimal, signed, whitespace-padded and scientific-notation values retain their numeric values."""
        assert build_datasets.nullable_number(value) == expected

    def test_zero_is_a_value_not_an_absence(self, build_datasets: ModuleType) -> None:
        # A plant genuinely rated at 0 MW must be distinguishable from one whose
        # rating the source never supplied.
        """An explicit zero rating remains distinguishable from an absent measurement."""
        assert build_datasets.nullable_number("0") == 0.0
        assert build_datasets.nullable_number("") is None

    def test_unparseable_input_raises_rather_than_silently_dropping(
        self, build_datasets: ModuleType
    ) -> None:
        """A nonnumeric source value raises ValueError instead of being discarded as missing."""
        with pytest.raises(ValueError):
            build_datasets.nullable_number("not a number")


class TestNormalizeStatus:
    """Source status vocabularies collapse onto the atlas status set."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("operating", "operational"),
            ("Operating", "operational"),
            ("operating_normally", "operational"),
            ("shut down", "shutdown"),
            ("Shut Down permanently", "shutdown"),
            ("commissioning", "commissioning"),
            ("commissioning phase", "commissioning"),
        ],
    )
    def test_known_vocabularies_map(
        self, build_datasets: ModuleType, raw: str, expected: str
    ) -> None:
        """Recognised source spellings map to the expected operational, shutdown or commissioning status."""
        assert build_datasets.normalize_status(raw) == expected

    def test_unknown_status_is_preserved_lowercased_not_discarded(
        self, build_datasets: ModuleType
    ) -> None:
        # Losing an unrecognised status would silently misreport a facility.
        """Unmapped statuses retain their lowercased original wording instead of an invented classification."""
        assert build_datasets.normalize_status("mothballed") == "mothballed"
        assert build_datasets.normalize_status("Under Construction") == "under construction"

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_absent_status_becomes_unknown(
        self, build_datasets: ModuleType, value: str | None
    ) -> None:
        """None and blank source statuses become the explicit unknown marker."""
        assert build_datasets.normalize_status(value) == "unknown"

    def test_underscores_are_treated_as_spaces(self, build_datasets: ModuleType) -> None:
        """The source spelling shut_down resolves to the same shutdown status as spaced wording."""
        assert build_datasets.normalize_status("shut_down") == "shutdown"


class TestNormalizedId:
    """Identifiers must be safe for DOM and query-string use."""

    def test_unsafe_characters_collapse(self, build_datasets: ModuleType) -> None:
        """Spaces and a slash in the source identifier become safe lowercased separators."""
        assert build_datasets.normalized_id("WRI GPPD/1019028") == "wri_gppd_1019028"

    def test_permitted_punctuation_survives(self, build_datasets: ModuleType) -> None:
        """Hyphen, colon, dot and underscore identity punctuation survives normalisation."""
        assert build_datasets.normalized_id("eea-ied:site.1_2") == "eea-ied:site.1_2"

    def test_leading_and_trailing_separators_are_trimmed(self, build_datasets: ModuleType) -> None:
        """Unsafe padding becomes separators that are removed only at the identifier boundaries."""
        assert build_datasets.normalized_id("  %%name%%  ") == "name"

    def test_distinct_sources_stay_distinct(self, build_datasets: ModuleType) -> None:
        # Over-aggressive collapsing would merge two unrelated facilities.
        """The tested distinct plant identifiers do not collide after normalisation."""
        assert build_datasets.normalized_id("plant a") != build_datasets.normalized_id("plant b")

    def test_is_idempotent(self, build_datasets: ModuleType) -> None:
        """Normalising the already-normalised source identifier changes no further bytes."""
        once = build_datasets.normalized_id("WRI GPPD/1019028")
        assert build_datasets.normalized_id(once) == once


class TestNormalizeCountry:
    """Aliases collapse for filtering while provenance is preserved elsewhere."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Czechia", "Czech Republic"),
            ("People's Republic of China", "China"),
            ("Türkiye", "Turkey"),
            ("United States of America", "United States"),
            ("EG", "Egypt"),
            ("LY", "Libya"),
        ],
    )
    def test_known_aliases_collapse(
        self, build_datasets: ModuleType, raw: str, expected: str
    ) -> None:
        """Declared country names and codes resolve to their tested canonical filter labels."""
        assert build_datasets.normalize_country(raw) == expected

    @pytest.mark.parametrize("value", [None, "", "   ", "unknown"])
    def test_absent_country_becomes_unknown(
        self, build_datasets: ModuleType, value: str | None
    ) -> None:
        """Missing, blank and explicitly unknown country cells retain the Unknown marker."""
        assert build_datasets.normalize_country(value) == "Unknown"

    def test_unmapped_country_passes_through_unchanged(self, build_datasets: ModuleType) -> None:
        # Rewriting an unrecognised country would fabricate a location.
        """An unmapped country name retains its original wording rather than a fabricated location."""
        assert build_datasets.normalize_country("Slovakia") == "Slovakia"


class TestReadTsv:
    """The TSV reader returns source rows verbatim."""

    def test_reads_rows_and_preserves_values(
        self, build_datasets: ModuleType, tmp_path: Path
    ) -> None:
        """The real TSV reader retains row order and exact source ID/name cells."""
        path = tmp_path / "rows.tsv"
        path.write_text("id\tname\n1\tAtucha I\n2\tArmenian-2\n", encoding="utf-8")
        rows = build_datasets.read_tsv(path)
        assert rows == [{"id": "1", "name": "Atucha I"}, {"id": "2", "name": "Armenian-2"}]

    def test_preserves_whitespace_and_unicode_in_source_values(
        self, build_datasets: ModuleType, tmp_path: Path
    ) -> None:
        # Source precision must survive: trimming here would alter the record.
        """Whitespace and Unicode in a source TSV cell survive the reader unchanged."""
        path = tmp_path / "rows.tsv"
        path.write_text("name\n Äänekoski \n", encoding="utf-8")
        assert build_datasets.read_tsv(path)[0]["name"] == " Äänekoski "

    def test_header_only_file_yields_no_rows(
        self, build_datasets: ModuleType, tmp_path: Path
    ) -> None:
        """A valid header with no data rows yields an empty record list."""
        path = tmp_path / "empty.tsv"
        path.write_text("id\tname\n", encoding="utf-8")
        assert build_datasets.read_tsv(path) == []


class TestEmit:
    """Datasets ship as JSON and as a browser-loadable JavaScript file."""

    def test_writes_both_representations_with_equal_content(
        self, build_datasets: ModuleType, tmp_path: Path
    ) -> None:
        """JSON and browser JavaScript carry identical records, count and schema metadata."""
        records = [{"id": "a", "name": "Äänekoski"}]
        build_datasets.emit("sample", "SAMPLE_GLOBAL", records, tmp_path)

        written = json.loads((tmp_path / "sample.json").read_text(encoding="utf-8"))
        # The record array is wrapped in an object, because the Tier-0 scaffold
        # profile requires an object at the top level of every repository JSON.
        assert written["records"] == records
        assert written["record_count"] == len(records)
        assert isinstance(written["schema_version"], str)

        js = (tmp_path / "sample.js").read_text(encoding="utf-8")
        assert js.startswith("window.SAMPLE_GLOBAL = ")
        # The JavaScript payload must carry exactly the JSON content, so the
        # two representations can never drift apart.
        payload = js[len("window.SAMPLE_GLOBAL = ") : -len(";\n")]
        assert json.loads(payload) == written

    def test_non_ascii_is_written_literally_not_escaped(
        self, build_datasets: ModuleType, tmp_path: Path
    ) -> None:
        """The emitted JSON retains literal Unicode source wording rather than escape sequences."""
        build_datasets.emit("sample", "SAMPLE_GLOBAL", [{"name": "Äänekoski"}], tmp_path)
        assert "Äänekoski" in (tmp_path / "sample.json").read_text(encoding="utf-8")
