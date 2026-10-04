# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete primary field projection contracts
"""Exercise source refusals and the whole original cohort through the public API and CLI.

Citation fixtures exercise syntax and preservation, not scientific acceptance of
an organisation, event, publisher body or licence. Baseline cells and their schema
are read from the actual production sources; they are never substituted by mocks.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "05_global_reactor_map/imports/research_reactors/official_source_enrichment"
sys.path.insert(0, str(DIR))
PROJECTION = importlib.import_module("projection")
BUILD = importlib.import_module("build_projection")
INTEGRATION = importlib.import_module(
    "05_global_reactor_map.imports.research_reactors.official_source_enrichment.integration"
)
SOURCE = DIR.parent / "research_reactors.tsv"


@pytest.fixture
def baseline() -> dict[str, dict[str, str]]:
    """Merge every original round so preservation tests cover the real 358-field cohort."""
    base = INTEGRATION.read_layer(SOURCE, ROOT)
    overlays = [
        INTEGRATION.read_layer(DIR.parent / directory / name, ROOT)
        for directory, name in (
            ("enrichment", "research_reactor_enrichment.tsv"),
            ("enrichment_round2", "research_reactor_enrichment_round2.tsv"),
            ("enrichment_round3", "research_reactor_enrichment_round3.tsv"),
            ("enrichment_round4", "research_reactor_enrichment_round4.tsv"),
            ("enrichment_round5", "research_reactor_enrichment_round5.tsv"),
        )
    ]
    return {
        identity: INTEGRATION.merge_layers(row, base, overlays)[0]
        for identity, row in base.rows.items()
    }


def ledger(baseline: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """Construct explicit no-fill contract decisions from the production column cohort.

    Parameters
    ----------
    baseline : dict of str to dict of str to str
        Real merged original rows; fixture decisions confer no scientific approval.

    Returns
    -------
    list of dict of str to str
        Exactly one contract decision per actual originally blank target cell.
    """
    return [
        {
            **dict.fromkeys(PROJECTION.COLUMNS, ""),
            "stable_id": identity,
            "field": field,
            "selection": "unknown",
            "scope": "Contract fixture: no source supplied; preserve the original blank.",
            "assertion_basis": "Fixture exercises no-fill behaviour, not scientific review.",
        }
        for identity, row in baseline.items()
        for field in PROJECTION.FIELDS
        if not row[field]
    ]


def citation(row: dict[str, str]) -> None:
    """Add a syntactically valid fixture citation without claiming original-body verification.

    Parameters
    ----------
    row : dict of str to str
        An actual-cohort fixture row, updated in place for source contract testing.
    """
    row.update(
        source_id="contract-fixture",
        source_title="Source syntax fixture, not accepted scientific evidence",
        source_url="https://example.org/research/source.html",
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        source_class="native_original_html",
        source_document_date="2025-06",
        source_capture_date="2026-10-03",
        locator="Contract fixture section",
        rights="Fixture does not grant publisher redistribution or licensing consent.",
    )


def inputs(tmp_path: Path, baseline: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    """Write exact full-cohort inputs for the same CLI users run.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Test-owned external workspace, physically supplied by the selected runtime.
    baseline : dict of str to dict of str to str
        Real baseline values and columns retained in the JSON input.

    Returns
    -------
    tuple of pathlib.Path
        Original baseline and complete field-ledger files.
    """
    base = tmp_path / "baseline.json"
    table = tmp_path / "fields.tsv"
    base.write_text(json.dumps({"rows": list(baseline.values())}), encoding="utf-8")
    with table.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=PROJECTION.COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(ledger(baseline))
    return base, table


def test_complete_real_cohort_retains_every_cell_and_source_decision(
    baseline: dict[str, dict[str, str]],
) -> None:
    """The API must not trade an absent field for a missing original record or provenance.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    """
    original = copy.deepcopy(baseline)
    fields = ledger(baseline)
    assert len(baseline) == 172 and len(fields) == 358
    selected = next(row for row in fields if row["field"] == "purpose")
    citation(selected)
    selected.update(selection="selected", value="Contract fixture exact value <&>")
    held = next(row for row in fields if row is not selected and row["field"] == "operator")
    citation(held)
    held.update(selection="held", value="Retained unresolved fixture role")
    result = PROJECTION.project_fields(baseline, fields)
    for identity, row in original.items():
        for field, value in row.items():
            expected = (
                selected["value"]
                if (identity, field) == (selected["stable_id"], "purpose")
                else value
            )
            assert result.rows[identity][field] == expected
    assert result.assertions == tuple(fields)
    assert baseline == original
    result.rows[selected["stable_id"]]["purpose"] = "Independent returned copy"
    assert baseline == original


@pytest.mark.parametrize(
    "precision,value", [("year", "1957"), ("month", "1957-08"), ("day", "1957-08-27")]
)
def test_event_precision_and_source_dates_remain_distinct(
    baseline: dict[str, dict[str, str]],
    precision: str,
    value: str,
) -> None:
    """A criticality assertion retains its exact precision and separate publisher/retrieval dates.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    precision : str
        Declared year, month or day precision for the retained criticality value.
    value : str
        Exact field or citation value selected by the parametrised case.
    """
    rows = ledger(baseline)
    row = next(r for r in rows if r["field"] == "first_criticality")
    citation(row)
    row.update(selection="selected", value=value, date_precision=precision)
    result = PROJECTION.project_fields(baseline, rows)
    assert result.rows[row["stable_id"]]["first_criticality"] == value
    assert result.assertions[rows.index(row)]["source_document_date"] == "2025-06"
    assert result.assertions[rows.index(row)]["source_capture_date"] == "2026-10-03"


@pytest.mark.parametrize(
    "key,value",
    [
        ("stable_id", ""),
        ("field", "capacity"),
        ("selection", "inferred"),
        ("scope", ""),
        ("assertion_basis", ""),
        ("locator", ""),
        ("source_sha256", "0"),
        ("source_class", "publisher_guess"),
        ("source_url", "http://example.org"),
        ("source_url", "https:///no-host"),
        ("source_url", "https://user@example.org"),
        ("source_url", "https://user:secret@example.org"),
        ("source_url", "https://example.org:0"),
        ("source_url", "https://example.org:65536"),
        ("source_url", "https://example.org:broken"),
        ("source_url", "https://[broken"),
        ("source_url", "https://example.org\\escape"),
        ("source_document_date", "2025/06"),
        ("source_document_date", "2025-02-30"),
        ("source_capture_date", "2026-13"),
        ("date_precision", "day"),
        ("value", "line\nbreak"),
        ("value", True),
    ],
)
def test_invalid_source_or_scientific_cells_refuse_before_projection(
    baseline: dict[str, dict[str, str]],
    key: str,
    value: object,
) -> None:
    """Malformed citation or cell values must never be promoted to a selected field.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    key : str
        Citation or scientific field changed in the owned input.
    value : object
        Exact field or citation value selected by the parametrised case.
    """
    row: dict[str, object] = dict(next(r for r in ledger(baseline) if r["field"] == "purpose"))
    citation_row = {k: str(v) for k, v in row.items()}
    citation(citation_row)
    citation_row.update(selection="selected", value="Fixture value")
    row = dict(citation_row)
    row[key] = value
    with pytest.raises(ValueError):
        PROJECTION.validate_assertion(row)


@pytest.mark.parametrize(
    "damage",
    [
        "column",
        "unknown_value",
        "held_without_source",
        "partial_citation",
        "selected_no_value",
        "selected_rendered",
        "precision",
        "bad_event",
    ],
)
def test_role_event_and_original_custody_guards(
    baseline: dict[str, dict[str, str]],
    damage: str,
) -> None:
    """A lead, unresolved role or mismatched event precision cannot become a scientific cell.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    damage : str
        Specific structural, custody, scientific-role or citation fault selected for the case.
    """
    row = dict(ledger(baseline)[0])
    if damage == "column":
        row.pop("rights")
    elif damage == "unknown_value":
        row["value"] = "Unjustified no-fill value"
    elif damage == "held_without_source":
        row.update(selection="held", value="Unbound retained claim")
    elif damage == "partial_citation":
        row["source_title"] = "Unbound source"
    else:
        citation(row)
        row.update(selection="selected", value="Fixture value")
        if damage == "selected_no_value":
            row["value"] = ""
        elif damage == "selected_rendered":
            row["source_class"] = "tool_rendered_author_page_lead"
        else:
            row.update(field="first_criticality", value="1962-03-27", date_precision="month")
            if damage == "bad_event":
                row["value"] = "1962-02-30"
    with pytest.raises(ValueError):
        PROJECTION.validate_assertion(row)


def test_https_port_and_source_less_hold_remain_explicit(
    baseline: dict[str, dict[str, str]],
) -> None:
    """Valid ports and empty held decisions are allowed without inventing a source or value.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    """
    row = ledger(baseline)[0]
    row["selection"] = "held"
    PROJECTION.validate_assertion(row)
    citation(row)
    row["source_url"] = "https://example.org:443/source"
    PROJECTION.validate_assertion(row)


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "unreviewed",
        "duplicate",
        "overwrite",
        "identity",
        "empty_baseline",
        "baseline_identity",
        "baseline_field",
    ],
)
def test_complete_original_cohort_is_required_for_any_selected_fill(
    baseline: dict[str, dict[str, str]],
    damage: str,
) -> None:
    """Partial ledgers and changes to nonempty original cells must refuse the whole projection.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    damage : str
        Specific structural, custody, scientific-role or citation fault selected for the case.
    """
    rows = ledger(baseline)
    if damage == "missing":
        rows.pop()
    elif damage == "unreviewed":
        rows[0]["selection"] = "unreviewed"
    elif damage == "duplicate":
        rows.append(dict(rows[0]))
    elif damage == "overwrite":
        identity, field = next(
            (i, f) for i, r in baseline.items() for f in PROJECTION.FIELDS if r[f]
        )
        rows[0].update(stable_id=identity, field=field)
    elif damage in {"identity", "extra"}:
        rows[0]["stable_id"] = "outside-original-cohort"
    elif damage == "empty_baseline":
        baseline = {}
    elif damage == "baseline_identity":
        next(iter(baseline.values()))["stable_id"] = "not-the-map-key"
    else:
        next(iter(baseline.values())).pop("operator")
    with pytest.raises(ValueError):
        PROJECTION.project_fields(baseline, rows)


@pytest.mark.parametrize("damage", ["empty", "header", "short", "long", "duplicate", "alias"])
def test_native_tsv_reader_preserves_complete_rows_or_refuses(
    tmp_path: Path,
    baseline: dict[str, dict[str, str]],
    damage: str,
) -> None:
    """The original TSV cannot silently lose cells, duplicate decisions or escape through an alias.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    damage : str
        Specific structural, custody, scientific-role or citation fault selected for the case.
    """
    _, path = inputs(tmp_path, baseline)
    lines = path.read_text().splitlines()
    if damage == "empty":
        lines = []
    elif damage == "header":
        lines[0] += "\tunbound"
    elif damage == "short":
        lines[1] = lines[1].rsplit("\t", 1)[0]
    elif damage == "long":
        lines[1] += "\textra"
    elif damage == "duplicate":
        lines.append(lines[1])
    else:
        alias = tmp_path / "alias.tsv"
        alias.symlink_to(path)
        path = alias
    if damage != "alias":
        path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError):
        PROJECTION.read_assertions(path)


def test_actual_cli_and_api_produce_identical_byte_bound_full_snapshots(
    tmp_path: Path,
    baseline: dict[str, dict[str, str]],
) -> None:
    """Users receive all172original records and358decisions with deterministic source digests.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    """
    base, table = inputs(tmp_path, baseline)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    one = BUILD.build_projection(base, table, first)
    result = subprocess.run(
        [
            sys.executable,
            str(DIR / "build_projection.py"),
            "--baseline",
            str(base),
            "--assertions",
            str(table),
            "--output",
            str(second),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == one
    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_bytes())
    assert document["rows"] == list(baseline.values())
    assert document["selected_fields"] == 0 and len(document["assertions"]) == 358
    assert document["baseline_sha256"] == hashlib.sha256(base.read_bytes()).hexdigest()
    assert document["ledger_sha256"] == hashlib.sha256(table.read_bytes()).hexdigest()
    assert one["sha256"] == hashlib.sha256(first.read_bytes()).hexdigest()
    with pytest.raises(OSError):
        BUILD.build_projection(base, table, first)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize(
    "body",
    [
        "null",
        "[]",
        '{"rows":false}',
        '{"rows":[null]}',
        '{"rows":[{"stable_id":"","operator":""}]}',
        '{"rows":[{"stable_id":"x","operator":false}]}',
        '{"rows":[{"stable_id":"x"},{"stable_id":"x"}]}',
    ],
)
def test_original_json_refuses_coercion_and_identity_loss(tmp_path: Path, body: str) -> None:
    """Non-string cells or duplicate identities are not a usable scientific baseline.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    body : str
        Complete negative-control JSON document whose structure or source bindings were changed.
    """
    path = tmp_path / "baseline.json"
    path.write_text(body)
    with pytest.raises(ValueError):
        BUILD.read_baseline(path)


def test_baseline_and_output_aliases_are_refused(
    tmp_path: Path, baseline: dict[str, dict[str, str]]
) -> None:
    """The CLI must not read or create source products through an aliased directory.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    """
    base, table = inputs(tmp_path, baseline)
    alias = tmp_path / "alias.json"
    alias.symlink_to(base)
    with pytest.raises(ValueError):
        BUILD.read_baseline(alias)
    parent = tmp_path / "alias-directory"
    parent.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        BUILD.build_projection(base, table, parent / "unexpected.json")
    assert not (tmp_path / "unexpected.json").exists()


def test_cli_refusal_has_no_interpreter_or_input_exception_text(tmp_path: Path) -> None:
    """Source failures map to one fixed refusal and leave no purported accepted output.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    """
    out = tmp_path / "refused.json"
    args = [
        "--baseline",
        str(tmp_path / "missing.json"),
        "--assertions",
        str(tmp_path / "missing.tsv"),
        "--output",
        str(out),
    ]
    result = subprocess.run(
        [sys.executable, str(DIR / "build_projection.py"), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "Research projection refused; check source bindings and complete field review.\n"
    )
    assert not out.exists()
    assert BUILD.main(args) == 2


@pytest.mark.parametrize(
    "source_class", ["native_original_facsimile", "native_discovery_registry_json"]
)
def test_original_image_is_selectable_but_discovery_registry_is_only_a_lead(
    baseline: dict[str, dict[str, str]],
    source_class: str,
) -> None:
    """An authentic facsimile is original evidence; a discovery identity cannot supply a fact.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    source_class : str
        Declared source category distinguishing original payloads from discovery leads.
    """
    row = ledger(baseline)[0]
    citation(row)
    row.update(source_class=source_class, selection="held", value="Fixture role")
    PROJECTION.validate_assertion(row)
    row["selection"] = "selected"
    if source_class == "native_discovery_registry_json":
        with pytest.raises(ValueError):
            PROJECTION.validate_assertion(row)
    else:
        PROJECTION.validate_assertion(row)


@pytest.mark.parametrize("selection", ["selected", "held"])
def test_future_criticality_is_retained_only_as_a_held_claim(
    baseline: dict[str, dict[str, str]],
    selection: str,
) -> None:
    """A forecast remains evidence but cannot become an actual event before its capture date.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    selection : str
        Field disposition used to distinguish a held forecast from a selected historical event.
    """
    row = next(r for r in ledger(baseline) if r["field"] == "first_criticality")
    citation(row)
    row.update(selection=selection, value="2036", date_precision="year")
    if selection == "selected":
        with pytest.raises(ValueError, match="future criticality"):
            PROJECTION.validate_assertion(row)
    else:
        PROJECTION.validate_assertion(row)


def test_package_api_resolves_without_a_sibling_module_alias(
    tmp_path: Path,
    baseline: dict[str, dict[str, str]],
) -> None:
    """The numeric-path package API must resolve its own projector just as the script CLI does.

    Parameters
    ----------
    tmp_path : Path
        Owned directory for real CLI inputs, outputs and source copies.
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    """
    base, table = inputs(tmp_path, baseline)
    out = tmp_path / "package-api.json"
    code = (
        "import importlib,json,sys;from pathlib import Path;"
        "module=importlib.import_module("
        "'05_global_reactor_map.imports.research_reactors.official_source_enrichment.build_projection');"
        "print(json.dumps(module.build_projection(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(base), str(table), str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["record_count"] == 172
    assert json.loads(out.read_bytes())["rows"] == list(baseline.values())


@pytest.mark.parametrize(
    "damage",
    ["valid", "empty", "object", "missing", "extra", "value", "blank", "url", "sha", "newline"],
)
def test_corroborating_and_conflicting_source_assertions_remain_bound(
    baseline: dict[str, dict[str, str]],
    damage: str,
) -> None:
    """Secondary source wording and disagreement survive; malformed or private-path bindings refuse.

    Parameters
    ----------
    baseline : dict[str, dict[str, str]]
        All 172 original merged source rows; nonempty cells must retain their values.
    damage : str
        Specific structural, custody, scientific-role or citation fault selected for the case.
    """
    row = ledger(baseline)[0]
    item: dict[str, object] = {
        "source_id": "corroborating-fixture",
        "original_url": "https://example.org/second",
        "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "reported_value": "Different original precision; no silent reconciliation",
        "admissibility": "Contract fixture retains the source assertion, not scientific approval.",
    }
    if damage == "object":
        row["related_evidence"] = json.dumps(item)
    elif damage == "empty":
        row["related_evidence"] = "[]"
    else:
        if damage == "missing":
            item.pop("source_id")
        elif damage == "extra":
            item["path"] = "/private/source"
        elif damage == "value":
            item["reported_value"] = 1961
        elif damage == "blank":
            item["source_id"] = ""
        elif damage == "url":
            item["original_url"] = "http://example.org/second"
        elif damage == "sha":
            item["sha256"] = "unbound"
        elif damage == "newline":
            item["reported_value"] = "unbound\nvalue"
        row["related_evidence"] = json.dumps([item])
    if damage in {"valid", "empty"}:
        PROJECTION.validate_assertion(row)
        rows = ledger(baseline)
        rows[0] = row
        assert (
            PROJECTION.project_fields(baseline, rows).assertions[0]["related_evidence"]
            == row["related_evidence"]
        )
    else:
        with pytest.raises(ValueError):
            PROJECTION.validate_assertion(row)
