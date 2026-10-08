# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_build_coverage.py

"""Tests for the field-completeness snapshot generator.

The coverage report is how the atlas exposes its own weaknesses, so a bug
that under-reports a gap would make the library look more complete than it
is. These tests therefore concentrate on the "is this field missing" decision.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_JSON = ROOT / "metadata" / "coverage_audit" / "coverage.json"


class TestMissing:
    """Absence detection drives every number in the report."""

    @pytest.mark.parametrize("value", [None, "", "   ", "\t", "\n"])
    def test_absent_values_are_missing(self, build_coverage: ModuleType, value: object) -> None:
        """None and empty or whitespace-only values are classified as missing."""
        assert build_coverage.missing(value) is True

    @pytest.mark.parametrize("value", ["0", 0, "unknown", "not provided", "n/a", False, "x"])
    def test_present_values_are_not_missing(
        self, build_coverage: ModuleType, value: object
    ) -> None:
        # A source that positively records "unknown" has supplied something;
        # treating that as absent would conflate two different facts.
        """Explicit zero, false and unknown/not-provided source markers count as present observations."""
        assert build_coverage.missing(value) is False

    def test_zero_is_present_not_missing(self, build_coverage: ModuleType) -> None:
        # A genuine zero capacity is data, not a gap.
        """Numeric and text zero remain present values rather than field gaps."""
        assert build_coverage.missing(0) is False
        assert build_coverage.missing("0") is False


class TestCounter:
    """Tallies must be deterministic so the report diffs cleanly."""

    def test_counts_by_field(self, build_coverage: ModuleType) -> None:
        """Actual field values are counted with one occurrence per supplied row."""
        rows = [{"domain": "fission"}, {"domain": "fusion"}, {"domain": "fission"}]
        assert build_coverage.counter(rows, "domain") == {"fission": 2, "fusion": 1}

    def test_absent_field_is_tallied_as_unknown(self, build_coverage: ModuleType) -> None:
        """Absent, blank and None field values share the explicit unknown tally."""
        rows = [{"domain": ""}, {}, {"domain": None}]
        assert build_coverage.counter(rows, "domain") == {"unknown": 3}

    def test_output_is_sorted_for_stable_diffs(self, build_coverage: ModuleType) -> None:
        """Tally keys are emitted in lexical order independently of input row ordering."""
        rows = [{"k": "z"}, {"k": "a"}, {"k": "m"}]
        assert list(build_coverage.counter(rows, "k")) == ["a", "m", "z"]

    def test_empty_input_yields_empty_tally(self, build_coverage: ModuleType) -> None:
        """An empty row sequence produces no field counts."""
        assert build_coverage.counter([], "domain") == {}


class TestPublishedCoverage:
    """The generated report must describe the data that is actually shipped."""

    def test_report_exists_and_parses(self) -> None:
        """The shipped coverage file exists and decodes as a JSON object."""
        assert COVERAGE_JSON.is_file()
        assert isinstance(json.loads(COVERAGE_JSON.read_text(encoding="utf-8")), dict)

    def test_report_totals_match_the_published_dataset(
        self, facilities: list[dict[str, object]]
    ) -> None:
        """The serialized shipped report contains the current facility-count digits."""
        report = json.loads(COVERAGE_JSON.read_text(encoding="utf-8"))
        totals = json.dumps(report)
        assert str(len(facilities)) in totals, "record total absent from the coverage report"

    def test_report_records_gaps_rather_than_hiding_them(self) -> None:
        # A coverage report with no gaps at all would mean the audit is not
        # actually inspecting fields.
        """The shipped report exposes the missing-field vocabulary to its readers."""
        report = json.loads(COVERAGE_JSON.read_text(encoding="utf-8"))
        flattened = json.dumps(report)
        assert "missing" in flattened


class TestRecordsOf:
    """Dataset documents and bare arrays must both be readable."""

    def test_unwraps_a_dataset_document(self, build_coverage: ModuleType) -> None:
        """A metadata-wrapped dataset yields its original record array."""
        document = {"schema_version": "1.0.0", "record_count": 1, "records": [{"id": "a"}]}
        assert build_coverage.records_of(document) == [{"id": "a"}]

    def test_accepts_a_bare_array(self, build_coverage: ModuleType) -> None:
        # Older exports, and any hand-written fixture, are still plain arrays.
        """The original plain-array representation remains readable without wrapping."""
        assert build_coverage.records_of([{"id": "a"}]) == [{"id": "a"}]

    def test_empty_document_yields_no_records(self, build_coverage: ModuleType) -> None:
        """Empty wrapped and plain-array datasets both yield an empty record sequence."""
        assert build_coverage.records_of({"records": []}) == []
        assert build_coverage.records_of([]) == []


@pytest.mark.parametrize("optimised", [False, True])
def test_native_report_preserves_counts_and_hidden_provenance(
    tmp_path: Path, optimised: bool
) -> None:
    """Normal/optimised native reports reproduce exact counts and Markdown bytes, including all seven legal header lines."""
    work = tmp_path / "unrelated"
    work.mkdir()
    output = tmp_path / "report"
    source_data = ROOT / "04_interactive_presentation" / "data"
    command = [sys.executable, *(["-O"] if optimised else [])]
    command.extend(
        [
            str(ROOT / "metadata" / "coverage_audit" / "build_coverage.py"),
            "--data-dir",
            str(source_data),
            "--out-dir",
            str(output),
        ]
    )
    process = subprocess.run(
        command, cwd=work, capture_output=True, text=True, check=False, timeout=30
    )
    assert process.returncode == 0, process.stderr
    assert process.stderr == ""
    report = json.loads((output / "coverage.json").read_text(encoding="utf-8"))
    accepted = json.loads(COVERAGE_JSON.read_text(encoding="utf-8"))
    assert report == accepted
    counts = json.loads(process.stdout)
    assert counts["facilities"] == report["facilities"]["records"]
    assert counts["mapped"] == report["facilities"]["mapped"]
    assert counts["companies"] == report["companies_and_programmes"]["records"]
    assert counts["taxonomy"] == report["taxonomy"]["records"]
    markdown = (output / "COVERAGE.md").read_text(encoding="utf-8")
    assert markdown.startswith("<!--\n")
    hidden, prose = markdown.split("-->", 1)
    fields = hidden.removeprefix("<!--\n").splitlines()
    assert len(fields) == 7
    assert fields[0] == (
        "SPDX-License-"  # Keep the report tag separate from this file licence.
        "Identifier: AGPL-3.0-or-later"
    )
    assert fields[-1] == "Atlas Reactorum — metadata/coverage_audit/COVERAGE.md"
    assert prose.startswith("\n\n# Atlas coverage audit\n")
    assert markdown == (ROOT / "metadata/coverage_audit/COVERAGE.md").read_text(encoding="utf-8")
