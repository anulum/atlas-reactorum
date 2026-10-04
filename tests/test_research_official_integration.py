# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — original research source integration conformance
"""Exercise complete original overlays and their actual release-builder consumer."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "05_global_reactor_map/imports/research_reactors/research_reactors.tsv"
OVERLAYS = [
    SOURCE.parent / directory / name
    for directory, name in [
        ("enrichment", "research_reactor_enrichment.tsv"),
        ("enrichment_round2", "research_reactor_enrichment_round2.tsv"),
        ("enrichment_round3", "research_reactor_enrichment_round3.tsv"),
        ("enrichment_round4", "research_reactor_enrichment_round4.tsv"),
        ("enrichment_round5", "research_reactor_enrichment_round5.tsv"),
    ]
]
INTEGRATION = importlib.import_module(
    "05_global_reactor_map.imports.research_reactors.official_source_enrichment.integration"
)


def test_every_original_row_preserves_all_accepted_urls_and_field_origins() -> None:
    """Merge all original rounds and retain earlier assertions independently of the selected scalar."""
    base = INTEGRATION.read_layer(SOURCE, ROOT)
    layers = [INTEGRATION.read_layer(path, ROOT) for path in OVERLAYS]
    assert len(base.rows) == 172
    assertions = 0
    previous = 0
    for identity, original in base.rows.items():
        row, urls, origins, applied = INTEGRATION.merge_layers(original, base, layers)
        originals = [layer for layer in [base, *layers] if identity in layer.rows]
        expected_urls = list(
            dict.fromkeys(layer.rows[identity]["source_url"] for layer in originals)
        )
        assert urls == expected_urls
        assert applied == (len(originals) > 1)
        for origin in origins:
            source = next(layer for layer in originals if layer.dataset == origin["source_dataset"])
            assert origin["source_sha256"] == source.sha256
            assert origin["value"] == source.rows[identity][origin["field"]]
            assert origin["source_url"] == source.rows[identity]["source_url"]
            if origin["selection"] == "selected":
                assert row[origin["field"]] == origin["value"]
            else:
                previous += 1
            assertions += 1
    expected_assertions = sum(
        bool(row.get(field))
        for layer in [base, *layers]
        for row in layer.rows.values()
        for field in ["operator", "purpose", "first_criticality"]
    )
    assert assertions == expected_assertions
    assert previous > 0
    hifar = base.rows["wikidata-q5642030"]
    _, urls, origins, _ = INTEGRATION.merge_layers(hifar, base, layers)
    assert any("arpansa.gov.au" in url for url in urls)
    assert any(origin["source_url"] in urls for origin in origins)


def test_real_release_cli_keeps_every_original_field_and_frozen_assertion(tmp_path: Path) -> None:
    """Run the real release CLI and permit primary additions only to originally blank cells.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    """
    shutil.copy2(
        ROOT / "04_interactive_presentation/data/facilities-supplemental.json",
        tmp_path / "facilities-supplemental.json",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "04_interactive_presentation/scripts/build_datasets.py"),
            "--data-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    document = json.loads((tmp_path / "global_reactors.sample.json").read_text())
    assert document["schema_version"] == "1.3.0"
    assert document["record_count"] == 13459
    published = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )
    assert document == published
    inventory = json.loads((tmp_path / "dataset-inventory.json").read_text())
    assert inventory["facility_field_assertions"] == 1631
    by_id = {row["id"]: row for row in document["records"]}
    base = INTEGRATION.read_layer(SOURCE, ROOT)
    layers = [INTEGRATION.read_layer(path, ROOT) for path in OVERLAYS]
    for identity, source in base.rows.items():
        row, urls, origins, _ = INTEGRATION.merge_layers(source, base, layers)
        built = by_id[identity]
        assert built["source_urls"][: len(urls)] == urls
        assert len(built["source_urls"]) == len(set(built["source_urls"]))
        supplemental = json.loads(
            (ROOT / "04_interactive_presentation/data/facilities-supplemental.json").read_text()
        )["records"]
        retained = {
            record["source_url"]
            for record in supplemental
            if record["name"].casefold().strip() == built["name"].casefold().strip()
            and record["domain"] == built["domain"]
        }
        primary = built.get("research_primary_assertions", [])
        retained.update(assertion["source_url"] for assertion in primary if assertion["source_url"])
        assert set(built["source_urls"][len(urls) :]) <= retained
        assert built.get("research_field_origins", []) == origins
        selected = {
            assertion["field"]: assertion["value"]
            for assertion in primary
            if assertion["selection"] == "selected"
        }
        for field in ["operator", "purpose", "first_criticality"]:
            if field in selected:
                assert row[field] == ""
                assert built[field] == selected[field]
            else:
                assert built[field] == row[field]


@pytest.mark.parametrize(
    "damage", ["empty", "header", "incomplete", "oversized", "duplicate", "blank_identity"]
)
def test_malformed_actual_source_refuses_instead_of_dropping_rows(
    tmp_path: Path, damage: str
) -> None:
    """Damage real source syntax or identity and require refusal rather than silent row loss.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    damage : str
        Selected incomplete or unreviewed input condition.
    """
    lines = SOURCE.read_text().splitlines()
    if damage == "empty":
        lines = []
    elif damage == "header":
        lines[0] = lines[0].replace("stable_id", "unbound_identity", 1)
    elif damage == "incomplete":
        lines[1] = lines[1].rsplit("\t", 1)[0]
    elif damage == "oversized":
        lines[1] += "\textra unbound source cell"
    elif damage == "duplicate":
        lines.append(lines[1])
    else:
        lines[1] = "\t" + lines[1].split("\t", 1)[1]
    damaged = tmp_path / "actual-research.tsv"
    damaged.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError):
        INTEGRATION.read_layer(damaged, tmp_path)


def test_native_source_symlink_is_not_an_original_table(tmp_path: Path) -> None:
    """Refuse an aliased table even when its bytes otherwise match the accepted input.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    """
    alias = tmp_path / "aliased-source.tsv"
    alias.symlink_to(SOURCE)
    with pytest.raises(ValueError, match="symlinks"):
        INTEGRATION.read_layer(alias, tmp_path)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.wikidata.org/wiki/Q3523626",
        "https://user@example.org/",
        "https://user:secret@example.org/",
        "relative/source",
        "https:///no-host",
        "",
    ],
)
def test_bad_original_source_url_refuses_the_public_merge_api(tmp_path: Path, url: str) -> None:
    """Reject unsafe source URLs through the public merge before accepting provenance.

    Parameters
    ----------
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    url : str
        Unsafe source URL used to exercise the public merge refusal.
    """
    with SOURCE.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)
    rows[0]["source_url"] = url
    path = tmp_path / "actual-source.tsv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or [], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    layer = INTEGRATION.read_layer(path, ROOT)
    assert layer.dataset == path.name
    original = next(iter(layer.rows.values()))
    with pytest.raises(ValueError):
        INTEGRATION.merge_layers(original, layer, [])


def test_changed_original_row_is_not_bound_by_a_matching_identity() -> None:
    """Detect changed source cells even when the stable identity still matches the original."""
    base = INTEGRATION.read_layer(SOURCE, ROOT)
    original = next(iter(base.rows.values()))
    changed = copy.deepcopy(original)
    changed["purpose"] = "changed original cell"
    with pytest.raises(ValueError, match="original base"):
        INTEGRATION.merge_layers(changed, base, [])
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == base.sha256


def test_repeated_actual_overlay_retains_each_source_url_once() -> None:
    """Replay an accepted overlay while keeping citation order and removing only duplicate links."""
    base = INTEGRATION.read_layer(SOURCE, ROOT)
    overlay = INTEGRATION.read_layer(OVERLAYS[0], ROOT)
    original = base.rows[next(iter(overlay.rows))]
    once = INTEGRATION.merge_layers(original, base, [overlay])
    twice = INTEGRATION.merge_layers(original, base, [overlay, overlay])
    assert twice[0] == once[0]
    assert twice[1] == once[1]
    assert len(twice[2]) > len(once[2])
    assert all(
        origin["source_sha256"] == overlay.sha256
        for origin in twice[2]
        if origin["source_dataset"] == overlay.dataset
    )
