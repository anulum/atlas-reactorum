# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_build_integration.py

"""End-to-end tests over the whole build chain.

Each builder runs as a real process against the repository's real source
catalogues, writing into a real directory, and its output is compared with the
dataset the atlas ships. Nothing is monkeypatched: the scripts take their roots
from the command line. A regression anywhere in the import, enrichment or
overlay chain fails here.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "04_interactive_presentation" / "data"
COVERAGE_DIR = ROOT / "metadata" / "coverage_audit"
DATASET_BUILDER = ROOT / "04_interactive_presentation" / "scripts" / "build_datasets.py"
COVERAGE_BUILDER = ROOT / "metadata" / "coverage_audit" / "build_coverage.py"


def run(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a build script as a real process.

    Parameters
    ----------
    script : pathlib.Path
        The script to run.
    *arguments : str
        Command-line arguments.

    Returns
    -------
    subprocess.CompletedProcess
        The finished process.
    """
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the datasets once, from the real sources, into a fresh directory."""
    out = tmp_path_factory.mktemp("rebuilt")
    # The supplemental layer is read from the output directory, so the real one
    # is copied in: this is the production input, not a stand-in.
    (out / "facilities-supplemental.json").write_bytes(
        (PUBLISHED / "facilities-supplemental.json").read_bytes()
    )
    result = run(DATASET_BUILDER, "--data-dir", str(out))
    assert result.returncode == 0, result.stderr[-3000:]
    return out


@pytest.fixture(scope="module")
def coverage_out(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run the coverage builder once into a fresh directory."""
    out = tmp_path_factory.mktemp("coverage")
    result = run(COVERAGE_BUILDER, "--out-dir", str(out))
    assert result.returncode == 0, result.stderr[-3000:]
    return out


class TestDatasetBuildReproduces:
    """The builder must reproduce the shipped datasets exactly."""

    @pytest.mark.parametrize("name", ["global_reactors.sample", "fusion_companies.sample"])
    def test_json_output_is_byte_identical_to_published(self, rebuilt: Path, name: str) -> None:
        assert (rebuilt / f"{name}.json").read_text(encoding="utf-8") == (
            PUBLISHED / f"{name}.json"
        ).read_text(encoding="utf-8")

    @pytest.mark.parametrize("name", ["global_reactors.sample", "fusion_companies.sample"])
    def test_javascript_output_is_byte_identical_to_published(
        self, rebuilt: Path, name: str
    ) -> None:
        assert (rebuilt / f"{name}.js").read_text(encoding="utf-8") == (
            PUBLISHED / f"{name}.js"
        ).read_text(encoding="utf-8")

    def test_record_count_matches_the_records_it_carries(self, rebuilt: Path) -> None:
        document = json.loads((rebuilt / "global_reactors.sample.json").read_text(encoding="utf-8"))
        assert document["record_count"] == len(document["records"])
        assert document["record_count"] == 13459

    def test_every_built_record_carries_provenance(self, rebuilt: Path) -> None:
        records: list[dict[str, Any]] = json.loads(
            (rebuilt / "global_reactors.sample.json").read_text(encoding="utf-8")
        )["records"]
        assert records, "builder produced no records"
        assert all(str(r.get("source_url", "")).startswith("http") for r in records)

    def test_all_depth_profiles_keep_current_fields_and_display_aliases_together(
        self, rebuilt: Path
    ) -> None:
        document = json.loads((rebuilt / "fusion_companies.sample.json").read_text())
        records = {row["name"]: row for row in document["records"]}
        count = 0
        for layer in (
            "depth_round4",
            "depth_round5",
            "depth_round6",
            "depth_round7",
            "depth_round8",
        ):
            path = ROOT / "metadata/company_audit" / layer / "enrichment_overlays.tsv"
            with path.open(newline="", encoding="utf-8") as handle:
                overlays = list(csv.DictReader(handle, delimiter="\t"))
            for overlay in overlays:
                count += 1
                record = records[overlay["organization"]]
                for field, display in (
                    ("normalized_status", "status_detail"),
                    ("highest_independently_supported_milestone", "independent_evidence"),
                    ("unsupported_or_ambiguous_claims", "data_caveat"),
                    ("official_url", "source_url"),
                    ("audit_date", "source_checked"),
                ):
                    assert record[field] == record[display], (layer, record["name"], field)
                assert record["source_dates"] == overlay["source_dates"]
                assert record["independent_urls"] == overlay["enriched_independent_urls"]
                assert record["source_urls"] == list(
                    dict.fromkeys(
                        [
                            record["source_url"],
                            *[
                                url.strip()
                                for url in overlay["enriched_independent_urls"].split(";")
                                if url.strip()
                            ],
                        ]
                    )
                )
        assert count == 39
        assert (
            "World Fusion Outlook 2024 (printed p. 21)" in records["Gauss Fusion"]["source_dates"]
        )

    def test_round8_preserves_actual_source_roles_and_unknown_prototype_fuel(
        self, rebuilt: Path
    ) -> None:
        document = json.loads((rebuilt / "fusion_companies.sample.json").read_text())
        records = {row["name"]: row for row in document["records"]}
        assert document["record_count"] == 98
        with (ROOT / "metadata/company_audit/depth_round8/enrichment_overlays.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            overlays = list(csv.DictReader(handle, delimiter="\t"))
        for overlay in overlays:
            record = records[overlay["organization"]]
            assert record["fuel_cycle"] == overlay["enriched_fuel_cycle"]
            assert (
                record["independent_evidence"]
                == overlay["enriched_highest_independently_supported_milestone"]
            )
            assert record["approach"] == overlay["enriched_approach_configuration"]
            assert record["public_devices_projects"] == overlay["enriched_named_devices_projects"]
            assert record["data_caveat"] == overlay["enriched_unsupported_or_ambiguous_claims"]
            assert record["source_checked"] == "2026-09-30"
            assert (
                record["depth_enrichment_source"]
                == "metadata/company_audit/depth_round8/enrichment_overlays.tsv"
            )
        assert (
            "HH70 working gas/isotope was not found" in records["Energy Singularity"]["fuel_cycle"]
        )
        assert "working gas or isotope is not established" in records["nT-Tao"]["fuel_cycle"]
        acceleron = records["Acceleron Fusion"]
        assert "933 MPa at 100 K" in acceleron["independent_evidence"]
        assert "not independent replication" in acceleron["independent_evidence"]
        assert "https://www.acceleronfusion.com/" not in acceleron["source_urls"]
        inventory = json.loads((rebuilt / "dataset-inventory.json").read_text())
        assert inventory["company_depth_round8_enrichments"] == 10
        assert "metadata/company_audit/depth_round8/enrichment_overlays.tsv" in inventory["inputs"]


class TestCoverageBuildReproduces:
    """The coverage audit must reproduce its published report."""

    def test_coverage_report_reproduces(self, coverage_out: Path) -> None:
        produced = json.loads((coverage_out / "coverage.json").read_text(encoding="utf-8"))
        shipped = json.loads((COVERAGE_DIR / "coverage.json").read_text(encoding="utf-8"))
        assert produced == shipped

    def test_coverage_markdown_reproduces(self, coverage_out: Path) -> None:
        assert (coverage_out / "COVERAGE.md").read_text(encoding="utf-8") == (
            COVERAGE_DIR / "COVERAGE.md"
        ).read_text(encoding="utf-8")

    def test_coverage_counts_agree_with_the_dataset(
        self, coverage_out: Path, facilities: list[dict[str, Any]]
    ) -> None:
        report = json.loads((coverage_out / "coverage.json").read_text(encoding="utf-8"))
        assert str(len(facilities)) in json.dumps(report)
