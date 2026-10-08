# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/test_build_guards.py

"""Tests for the builder's fail-closed guards and optional-source handling.

Every test here runs the real build script as a real process, against a real
directory tree assembled from the repository's own catalogues. Nothing is
monkeypatched and nothing is stubbed: the builder takes its roots from
``--source-root`` and ``--data-dir``, so a test varies its inputs by writing
real files rather than by substituting module state.

The guards matter because each replaced an ``assert``, which ``python -O``
strips. A stripped duplicate-identifier check would let two facilities collide
silently in the published dataset.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from ._source_shape import (
    COMPANY_COLUMNS,
    COMPANY_SAMPLE_ROW,
    FACILITY_COLUMNS,
    FUSION_COLUMNS,
    FUSION_SAMPLE_ROW,
    RESEARCH_COLUMNS,
    RESEARCH_SAMPLE_ROW,
)

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "04_interactive_presentation" / "scripts" / "build_datasets.py"
FACILITY_RELATIVE = Path("05_global_reactor_map/data/reactors.tsv")

# Inputs the builder reads unconditionally, copied verbatim from the
# repository so the tree under test is real in every respect except the one
# layer a test deliberately varies.
REQUIRED_INPUTS = (Path("metadata/discovery_audit/fusion_companies_candidates.tsv"),)

DEFAULTS = {
    "record_kind": "facility",
    "domain": "nuclear_fission",
    "reactor_type": "test reactor",
    "status": "operating",
    "evidence_maturity": "established",
    "country": "Nowhere",
    "country_code": "NW",
    "latitude": "10.0",
    "longitude": "20.0",
    "last_verified": "2026-09-26",
}

FACILITY_HEADER = "\t".join(FACILITY_COLUMNS) + "\n"


def facility_row(identifier: str, url: str = "https://example.org/record", **overrides: str) -> str:
    """Serialize one facility row in the production column order.

    Parameters
    ----------
    identifier : str
        Facility ID, also used to construct the default display name.
    url : str
        Provenance URL to place in the source row.
    **overrides : str
        Source cells that replace the default values for a guard scenario.

    Returns
    -------
    str
        Tab-separated row, including its trailing newline; the header is separate.
    """
    values = dict.fromkeys(FACILITY_COLUMNS, "")
    values.update(DEFAULTS)
    values["id"] = identifier
    values["name"] = f"Site {identifier}"
    values["source_url"] = url
    values.update(overrides)
    return "\t".join(values[column] for column in FACILITY_COLUMNS) + "\n"


@pytest.fixture
def tree(tmp_path: Path) -> Iterator[Path]:
    """Yield an owned source tree with mandatory inputs and no optional layers.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Parent of the temporary source root and sibling output directory.

    Yields
    ------
    pathlib.Path
        Source root carrying the real company catalogue. Its sibling data directory
        contains an empty supplemental document, so missing layers add no records.

    Notes
    -----
    The source tree is removed after the test; repository catalogues are copied only.
    """
    root = tmp_path / "source"
    (root / FACILITY_RELATIVE.parent).mkdir(parents=True)
    for relative in REQUIRED_INPUTS:
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, root / relative)
    data = tmp_path / "data"
    data.mkdir()
    # The supplemental layer is read unconditionally; an empty document is the
    # honest representation of a tree carrying no supplemental context.
    (data / "facilities-supplemental.json").write_text(
        json.dumps({"schema_version": "1.0.0", "record_count": 0, "records": []}) + "\n",
        encoding="utf-8",
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def run_builder(tree: Path, rows: str, *flags: str) -> subprocess.CompletedProcess[str]:
    """Write a facility catalogue into the tree and run the real builder.

    Parameters
    ----------
    tree : pathlib.Path
        The source root produced by the ``tree`` fixture.
    rows : str
        Complete contents of the facility catalogue, header included.
    *flags : str
        Extra interpreter flags, such as ``-O``.

    Returns
    -------
    subprocess.CompletedProcess
        The finished build process.
    """
    (tree / FACILITY_RELATIVE).write_text(rows, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            *flags,
            str(BUILDER),
            "--fusion-source",
            "historical",
            "--source-root",
            str(tree),
            "--data-dir",
            str(tree.parent / "data"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )


def built_records(tree: Path) -> list[dict[str, object]]:
    """Read facility records from this test's generated output document.

    Parameters
    ----------
    tree : pathlib.Path
        Owned source root whose sibling data directory holds the builder outputs.

    Returns
    -------
    list of dict
        Records loaded from global_reactors.sample.json.
    """
    document = json.loads(
        (tree.parent / "data" / "global_reactors.sample.json").read_text(encoding="utf-8")
    )
    records: list[dict[str, object]] = document["records"]
    return records


class TestOptionalLayersAreSkipped:
    """A missing optional layer is skipped, never fabricated."""

    def test_build_succeeds_with_only_the_base_layer(self, tree: Path) -> None:
        """Build exactly two base facilities when every optional facility layer is absent."""
        result = run_builder(tree, FACILITY_HEADER + facility_row("a1") + facility_row("a2"))
        assert result.returncode == 0, result.stderr[-2000:]
        assert len(built_records(tree)) == 2

    def test_absent_layers_contribute_nothing(self, tree: Path) -> None:
        """Keep only the supplied base facility when optional layers are absent."""
        result = run_builder(tree, FACILITY_HEADER + facility_row("solo"))
        assert result.returncode == 0, result.stderr[-2000:]
        records = built_records(tree)
        assert len(records) == 1
        assert records[0]["name"] == "Site solo"


class TestFailClosedGuards:
    """An invariant violation must fail the build, including under ``-O``."""

    def test_duplicate_facility_identifier_is_rejected(self, tree: Path) -> None:
        """Fail the real build with the duplicate-facility identifier diagnostic."""
        result = run_builder(tree, FACILITY_HEADER + facility_row("dup-1") + facility_row("dup-1"))
        assert result.returncode != 0
        assert "Duplicate facility ID" in result.stderr

    def test_non_http_source_url_is_rejected(self, tree: Path) -> None:
        """Reject an FTP provenance URL with the HTTP diagnostic."""
        rows = FACILITY_HEADER + facility_row("ok1") + facility_row("bad1", url="ftp://x/y")
        result = run_builder(tree, rows)
        assert result.returncode != 0
        assert "HTTP" in result.stderr

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("latitude", "91.0"),
            ("latitude", "-91.0"),
            ("longitude", "181.0"),
            ("longitude", "-181.0"),
        ],
    )
    def test_coordinate_outside_the_globe_is_rejected(
        self, tree: Path, field: str, value: str
    ) -> None:
        """Reject each latitude or longitude outside its geographic bounds."""
        result = run_builder(tree, FACILITY_HEADER + facility_row("bad", **{field: value}))
        assert result.returncode != 0
        assert "coordinate out of range" in result.stderr

    def test_guards_survive_optimised_bytecode(self, tree: Path) -> None:
        # `assert` is stripped by -O. Running the real builder under -O with a
        # duplicate proves the guards are statements, not assertions.
        """Reject duplicate facility identifiers when the real builder runs under -O."""
        result = run_builder(
            tree, FACILITY_HEADER + facility_row("dup-2") + facility_row("dup-2"), "-O"
        )
        assert result.returncode != 0, "the duplicate guard vanished under -O"
        assert "Duplicate facility ID" in result.stderr


def _one_row(path: Path, columns: list[str], sample: dict[str, str]) -> Path:
    """Write one source row and header using the production column order.

    Parameters
    ----------
    path : pathlib.Path
        Owned catalogue destination; missing parent directories are created.
    columns : list of str
        Ordered source columns for the selected catalogue layer.
    sample : dict of str to str
        Sample cells; absent column values serialize as empty strings.

    Returns
    -------
    pathlib.Path
        The written catalogue path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\t".join(columns) + "\n"
    row = "\t".join(sample.get(column, "") for column in columns) + "\n"
    path.write_text(header + row, encoding="utf-8")
    return path


class TestPartialCheckout:
    """The ordinary source-root API keeps partial caller-owned tree support."""

    """A base layer present without its enrichment rounds must still build.

    This is the shape of a checkout where a later round has not been fetched.
    The enrichment loops must skip the absent rounds rather than failing, or
    silently dropping the base layer they belong to.
    """

    def test_base_layers_build_without_their_enrichment_rounds(self, tree: Path) -> None:
        """Retain base, fusion and research rows without optional enrichment directories."""
        _one_row(
            tree / "05_global_reactor_map/imports/fusion/fusion_facilities.tsv",
            FUSION_COLUMNS,
            FUSION_SAMPLE_ROW,
        )
        _one_row(
            tree / "05_global_reactor_map/imports/research_reactors/research_reactors.tsv",
            RESEARCH_COLUMNS,
            RESEARCH_SAMPLE_ROW,
        )
        result = run_builder(tree, FACILITY_HEADER + facility_row("base-1"))
        assert result.returncode == 0, result.stderr[-2000:]
        names = {str(record["name"]) for record in built_records(tree)}
        assert "Site base-1" in names, "the base facility layer was dropped"
        assert len(built_records(tree)) == 3, "expected base, fusion and research rows"


class TestSupplementalLayerForms:
    """The supplemental layer is accepted in either published form."""

    def test_a_bare_array_supplemental_is_still_read(self, tree: Path) -> None:
        # Datasets published before the object wrapper are plain arrays. A
        # checkout carrying one must still build rather than crash.
        """Accept an empty legacy supplemental array and retain the single base facility."""
        (tree.parent / "data" / "facilities-supplemental.json").write_text(
            json.dumps([]) + "\n", encoding="utf-8"
        )
        result = run_builder(tree, FACILITY_HEADER + facility_row("bare-1"))
        assert result.returncode == 0, result.stderr[-2000:]
        assert len(built_records(tree)) == 1


class TestCompanyGuards:
    """Company records must stay individually addressable."""

    def test_duplicate_company_name_is_rejected(self, tree: Path) -> None:
        """Reject duplicated company source rows with the duplicate-name diagnostic."""
        columns = COMPANY_COLUMNS
        header = "\t".join(columns) + "\n"
        duplicated = dict(COMPANY_SAMPLE_ROW)
        duplicated["company"] = "Twice Listed"
        row = "\t".join(duplicated.get(column, "") for column in columns) + "\n"
        (tree / "metadata/discovery_audit/fusion_companies_candidates.tsv").write_text(
            header + row + row, encoding="utf-8"
        )
        result = run_builder(tree, FACILITY_HEADER + facility_row("c1"))
        assert result.returncode != 0
        assert "Duplicate company name" in result.stderr
