# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Wikidata research-reactor producer conformance

"""Exercise the complete captured query through offline and actual TLS surfaces."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
import urllib.parse
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from ._catalogue_inputs import ROOT
from .conftest import load_module
from .test_public_reactor_repository_build import api_body, api_server
from .test_public_reactor_repository_build import certificate as certificate

DIRECTORY = ROOT / "05_global_reactor_map/imports/research_reactors"
SCRIPT = DIRECTORY / "scripts/fetch_wikidata_research_reactors.py"
FIXTURE = ROOT / "tests/data/research_reactors_wikidata"


@pytest.fixture
def producer() -> ModuleType:
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_research_fetcher")


def sources() -> dict[str, Any]:
    """Read the complete captured discovery/core/reference source envelope."""
    document: dict[str, Any] = json.loads((FIXTURE / "cache.json").read_bytes())
    return document


def rows(body: bytes) -> list[dict[str, str]]:
    """Decode the actual generated table with its published TSV header."""
    return list(csv.DictReader(io.StringIO(body.decode()), delimiter="\t"))


def first_claim(document: dict[str, Any], prop: str) -> dict[str, Any]:
    """Find an existing captured claim for an explicit source-cell mutation."""
    return next(c for e in document["core"].values() for c in e["claims"].get(prop, []))


def routes(
    producer: ModuleType, document: dict[str, Any]
) -> dict[str, tuple[int, dict[str, str], bytes, float]]:
    """Expose every complete genuine batch at the production API query paths."""
    result: dict[str, tuple[int, dict[str, str], bytes, float]] = {
        "/query?" + urllib.parse.urlencode({"query": producer.QUERY, "format": "json"}): (
            200,
            {},
            api_body(document["discovery"]),
            0.0,
        )
    }
    for name, props, languages in [
        ("core", "labels|aliases|claims", None),
        ("labels", "labels", "en|mul|de|fr|es|ru"),
    ]:
        ids = sorted(document[name], key=lambda q: int(q[1:]))
        for start in range(0, len(ids), 50):
            batch = ids[start : start + 50]
            params = {
                "action": "wbgetentities",
                "format": "json",
                "formatversion": "2",
                "ids": "|".join(batch),
                "props": props,
            }
            if languages:
                params.update(languages=languages, languagefallback="1")
            result["/entities?" + urllib.parse.urlencode(params)] = (
                200,
                {},
                api_body({"entities": {qid: document[name][qid] for qid in batch}}),
                0.0,
            )
    return result


def test_every_captured_cell_and_historical_row(producer: ModuleType, tmp_path: Path) -> None:
    metadata = json.loads((FIXTURE / "SOURCE.json").read_bytes())
    assert (
        hashlib.sha256((FIXTURE / "cache.json").read_bytes()).hexdigest()
        == metadata["fixture_sha256"]
    )
    document = sources()
    assert len(document["discovery"]["results"]["bindings"]) == 166
    assert len(document["core"]) == 161 and len(document["labels"]) == 75
    expected = [
        r
        for r in csv.DictReader((DIRECTORY / "research_reactors.tsv").open(), delimiter="\t")
        if r["stable_id"].startswith("wikidata-")
    ]
    body = producer.render(document, retrieved="2026-09-26")
    assert {r["stable_id"]: r for r in rows(body)} == {r["stable_id"]: r for r in expected}
    assert all(r["thermal_power_mw"] == r["first_criticality"] == "" for r in rows(body))
    candidate = tmp_path / "candidate.tsv"
    producer.build(document, candidate, retrieved="2026-09-26")
    merged = tmp_path / "merged.tsv"
    for command in [
        [
            str(DIRECTORY / "scripts/merge_supplements.py"),
            str(candidate),
            str(DIRECTORY / "supplements/cnsc_official.tsv"),
            "--out",
            str(merged),
        ],
        [str(DIRECTORY / "scripts/validate.py"), str(merged)],
    ]:
        result = subprocess.run(
            [sys.executable, *command], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert merged.read_bytes() == (DIRECTORY / "research_reactors.tsv").read_bytes()


@pytest.mark.parametrize("optimized", [False, True])
def test_native_offline_complete_cache(
    producer: ModuleType, tmp_path: Path, optimized: bool
) -> None:
    output = tmp_path / "candidate.tsv"
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimized else []),
            str(SCRIPT),
            "--cache",
            str(FIXTURE / "cache.json"),
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert {r["retrieved"] for r in rows(output.read_bytes())} == {"2026-09-30"}


@pytest.mark.parametrize("native", [False, True])
def test_actual_tls_full_refresh(
    producer: ModuleType, tmp_path: Path, certificate: tuple[Path, Path], native: bool
) -> None:
    document = sources()
    with api_server(certificate, routes(producer, document)) as (base, requests):
        host = base.removesuffix("/repos")
        output = tmp_path / "candidate.tsv"
        cache = tmp_path / "cache.json"
        args = [
            "--refresh",
            "--out",
            str(output),
            "--cache-out",
            str(cache),
            "--query-url",
            host + "/query",
            "--entity-url",
            host + "/entities",
            "--ca-file",
            str(certificate[0]),
        ]
        if native:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
            )
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert producer.main(args) == 0
        assert len(requests) == 7
        assert len(rows(output.read_bytes())) == 161
        saved = json.loads(cache.read_bytes())
        assert saved["captured_at"] == date.today().isoformat()
        assert saved["core"] == document["core"] and saved["labels"] == document["labels"]


@pytest.mark.parametrize(
    "label,status",
    [
        ("inactive", "shutdown"),
        ("not operational", "shutdown"),
        ("operating", "operational"),
        ("under construction", "under_construction"),
        ("decommissioning", "decommissioning"),
        ("planned", "planned"),
        ("abandoned", "cancelled"),
        ("unclassified", "unknown"),
    ],
)
def test_status_is_explicit_source_label(producer: ModuleType, label: str, status: str) -> None:
    document = sources()
    reactor = next(
        e
        for e in document["core"].values()
        if e["claims"].get("P5817") and not e["claims"].get("P576") and not e["claims"].get("P730")
    )
    claim = reactor["claims"]["P5817"][0]
    qid = claim["mainsnak"]["datavalue"]["value"]["id"]
    document["labels"][qid]["labels"] = {"en": {"language": "en", "value": label}}
    actual = next(
        r
        for r in rows(producer.render(document, retrieved="2026-09-26"))
        if r["stable_id"] == "wikidata-" + reactor["id"].lower()
    )
    assert actual["status"] == status
    assert f"raw status label: {label}." in actual["verification_notes"]


@pytest.mark.parametrize(
    "corruption",
    [
        "version",
        "date",
        "binding",
        "duplicate",
        "uri",
        "core",
        "id",
        "missing",
        "labels",
        "aliases",
        "claims",
        "rank",
        "snak",
        "datavalue",
        "reference",
        "nan",
        "bool",
        "range",
        "globe",
        "time",
        "precision",
    ],
)
def test_complete_source_corruption_refused_before_write(
    producer: ModuleType, tmp_path: Path, corruption: str
) -> None:
    document = sources()
    entity = next(iter(document["core"].values()))
    if corruption == "version":
        document["schema_version"] = "2"
    elif corruption == "date":
        document["captured_at"] = "20260930"
    elif corruption == "binding":
        document["discovery"]["results"]["bindings"][0] = None
    elif corruption == "duplicate":
        document["discovery"]["results"]["bindings"].append(
            document["discovery"]["results"]["bindings"][0]
        )
    elif corruption == "uri":
        document["discovery"]["results"]["bindings"][0]["item"]["value"] = (
            "https://example.org/entity/Q1"
        )
    elif corruption == "core":
        document["core"].pop(entity["id"])
    elif corruption == "id":
        entity["id"] = "Q1"
    elif corruption == "missing":
        entity["missing"] = True
    elif corruption == "labels":
        entity["labels"] = {"en": {"value": ""}}
    elif corruption == "aliases":
        entity["aliases"] = {"en": [1]}
    elif corruption == "claims":
        entity["claims"] = []
    elif corruption in {"rank", "snak", "datavalue", "reference"}:
        claim = first_claim(document, "P17")
        if corruption == "rank":
            claim["rank"] = "invalid"
        elif corruption == "snak":
            claim["mainsnak"]["snaktype"] = "invalid"
        elif corruption == "datavalue":
            claim["mainsnak"]["datavalue"] = []
        else:
            claim["mainsnak"]["datavalue"]["value"]["id"] = "bad"
    elif corruption in {"nan", "bool", "range", "globe"}:
        value = first_claim(document, "P625")["mainsnak"]["datavalue"]["value"]
        if corruption == "globe":
            value["globe"] = "http://www.wikidata.org/entity/Q111"
        else:
            value["latitude"] = {"nan": float("nan"), "bool": True, "range": 91}[corruption]
    else:
        value = first_claim(document, "P576")["mainsnak"]["datavalue"]["value"]
        value["time" if corruption == "time" else "precision"] = None
    output = tmp_path / "candidate.tsv"
    output.write_bytes(b"previous reviewed candidate")
    with pytest.raises((ValueError, TypeError)):
        producer.build(document, output, retrieved="2026-09-26")
    assert output.read_bytes() == b"previous reviewed candidate"
    assert list(tmp_path.iterdir()) == [output]


@pytest.mark.parametrize(
    "body,status", [(b"{", 200), (b"[]", 200), (b'{"error":{}}', 200), (b"{}", 201), (b"{}", 503)]
)
def test_real_response_failures(
    producer: ModuleType, certificate: tuple[Path, Path], body: bytes, status: int
) -> None:
    with api_server(certificate, {"/repos": (status, {}, body, 0.0)}) as (url, requests):
        with pytest.raises((ValueError, RuntimeError)):
            producer.get_json(url, ca_file=certificate[0], attempts=2, backoff=0)
        assert len(requests) == (2 if status == 503 else 1)


def test_real_certificate_and_byte_limits(
    producer: ModuleType, certificate: tuple[Path, Path]
) -> None:
    with api_server(certificate, {"/repos": (200, {}, b'{"value":12}', 0.0)}) as (url, requests):
        with pytest.raises(RuntimeError):
            producer.get_json(url, attempts=1)
        assert not requests
        with pytest.raises(ValueError, match="byte limit"):
            producer.get_json(url, ca_file=certificate[0], max_bytes=4)
        assert len(requests) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--cache-out", "other.json"],
        ["--refresh"],
        ["--query-url", "https://example.org"],
        ["--ca-file", "missing.pem"],
    ],
)
def test_native_mode_requires_explicit_inputs(
    producer: ModuleType, tmp_path: Path, arguments: list[str]
) -> None:
    output = tmp_path / "candidate.tsv"
    assert producer.main(["--out", str(output), *arguments]) == 1
    assert not output.exists()


def test_protect_input_and_library(producer: ModuleType, tmp_path: Path) -> None:
    source = tmp_path / "cache.json"
    source.write_bytes((FIXTURE / "cache.json").read_bytes())
    original = source.read_bytes()
    assert producer.main(["--cache", str(source), "--out", str(source)]) == 1
    assert source.read_bytes() == original
    with pytest.raises(ValueError):
        producer.build(sources(), DIRECTORY / "research_reactors.tsv", retrieved="2026-09-26")


def synchronize_reference_cache(producer: ModuleType, document: dict[str, Any]) -> None:
    """Retain the captured labels still consumed after an explicit cell mutation."""
    expected = producer.referenced_ids(producer.discover(document["discovery"]), document["core"])
    original = sources()
    document["labels"] = {
        qid: document["labels"].get(qid, original["labels"][qid]) for qid in expected
    }


@pytest.mark.parametrize(
    "change",
    [
        "preferred",
        "deprecated",
        "somevalue",
        "novalue",
        "no-label",
        "invalid-time",
        "coarse-time",
        "conflicting-status",
    ],
)
def test_source_rank_absence_and_ambiguity_preserve_unknown(
    producer: ModuleType, change: str
) -> None:
    document = sources()
    entity = next(
        e
        for e in document["core"].values()
        if e["claims"].get("P17")
        and e["claims"].get("P5817")
        and not e["claims"].get("P576")
        and not e["claims"].get("P730")
    )
    country = entity["claims"]["P17"][0]
    if change in {"preferred", "deprecated"}:
        country["rank"] = change
    elif change in {"somevalue", "novalue"}:
        country["mainsnak"] = {"snaktype": change}
    elif change == "no-label":
        entity["labels"] = {}
    elif change in {"invalid-time", "coarse-time"}:
        entity = next(e for e in document["core"].values() if e["claims"].get("P576"))
        value = entity["claims"]["P576"][0]["mainsnak"]["datavalue"]["value"]
        if change == "invalid-time":
            value["time"] = "source date unavailable"
        else:
            value["precision"] = 8
    else:
        claim = entity["claims"]["P5817"][0]
        status = claim["mainsnak"]["datavalue"]["value"]["id"]
        other = next(q for q in document["labels"] if q != status)
        document["labels"][status]["labels"] = {"en": {"value": "active"}}
        document["labels"][other]["labels"] = {"en": {"value": "inactive"}}
        additional = json.loads(json.dumps(claim))
        additional["mainsnak"]["datavalue"]["value"]["id"] = other
        entity["claims"]["P5817"].append(additional)
    synchronize_reference_cache(producer, document)
    actual = next(
        r
        for r in rows(producer.render(document, retrieved="2026-09-26"))
        if r["stable_id"] == "wikidata-" + entity["id"].lower()
    )
    if change in {"deprecated", "somevalue", "novalue"}:
        assert actual["country"] == ""
    elif change == "preferred":
        assert actual["country"]
    elif change == "no-label":
        assert actual["name"] == entity["id"]
    elif change == "conflicting-status":
        assert actual["status"] == "unknown"
    else:
        assert actual["shutdown_date"] == ""


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/repos",
        "https://user:password@localhost/repos",
        "https://localhost:0/repos",
        "https://localhost/repos#fragment",
        "https://local host/repos",
        "https:///repos",
    ],
)
def test_source_urls_refused_before_network(producer: ModuleType, url: str) -> None:
    with pytest.raises(ValueError):
        producer.get_json(url)


@pytest.mark.parametrize(
    "limits",
    [
        {"attempts": 0},
        {"attempts": 5},
        {"attempts": True},
        {"timeout": float("inf")},
        {"timeout": 0},
        {"max_bytes": 0},
        {"max_bytes": 2.5},
        {"backoff": float("nan")},
        {"backoff": 2},
    ],
)
def test_request_limits_refuse_unbounded_settings(
    producer: ModuleType, limits: dict[str, Any]
) -> None:
    with pytest.raises(ValueError):
        producer.get_json("https://localhost/repos", **limits)


@pytest.mark.parametrize("redirect", ["relative", "insecure"])
def test_actual_server_redirect_validation(
    producer: ModuleType, certificate: tuple[Path, Path], redirect: str
) -> None:
    location = "/target" if redirect == "relative" else "http://localhost/target"
    with api_server(
        certificate,
        {
            "/repos": (302, {"Location": location}, b"", 0.0),
            "/target": (200, {}, b'{"complete":true}', 0.0),
        },
    ) as (url, requests):
        if redirect == "relative":
            assert producer.get_json(url, ca_file=certificate[0]) == {"complete": True}
        else:
            with pytest.raises(ValueError):
                producer.get_json(url, ca_file=certificate[0])
        assert len(requests) == (2 if redirect == "relative" else 1)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"results": {}},
        {"results": {"bindings": []}},
        {"results": {"bindings": [{"item": {"type": "literal", "value": "Q1"}}]}},
    ],
)
def test_incomplete_discovery_refused(
    producer: ModuleType, tmp_path: Path, payload: object
) -> None:
    document = sources()
    document["discovery"] = payload
    with pytest.raises(ValueError):
        producer.build(document, tmp_path / "candidate.tsv", retrieved="2026-09-26")
    assert not (tmp_path / "candidate.tsv").exists()


@pytest.mark.parametrize("size", [0, 51])
def test_public_entity_batch_bounds(producer: ModuleType, size: int) -> None:
    with pytest.raises(ValueError):
        list(producer.chunks(list(sources()["core"]), size))


def test_public_entity_identity_acquisition_refusal(producer: ModuleType) -> None:
    identities = set(sources()["core"])
    identities.add("bad")
    with pytest.raises(ValueError):
        producer.fetch_entities(identities)


def test_missing_claim_value_and_noncanonical_row_date(
    producer: ModuleType, tmp_path: Path
) -> None:
    document = sources()
    first_claim(document, "P17")["mainsnak"]["datavalue"]["value"] = None
    with pytest.raises(ValueError):
        producer.build(document, tmp_path / "candidate.tsv", retrieved="2026-09-26")
    with pytest.raises(ValueError):
        producer.build(sources(), tmp_path / "candidate.tsv", retrieved="20260926")


def test_actual_socket_timeout_is_bounded(
    producer: ModuleType, certificate: tuple[Path, Path]
) -> None:
    with api_server(certificate, {"/repos": (200, {}, b"{}", 0.1)}) as (url, requests):
        with pytest.raises(RuntimeError):
            producer.get_json(url, ca_file=certificate[0], attempts=1, timeout=0.01)
        assert requests == ["/repos"]


@pytest.mark.parametrize("part", ["core", "labels"])
def test_actual_partial_batch_refused_before_either_output(
    producer: ModuleType, tmp_path: Path, certificate: tuple[Path, Path], part: str
) -> None:
    document = sources()
    served = routes(producer, document)
    key = next(
        key
        for key in served
        if key.startswith("/entities?")
        and (
            "props=labels&" in key if part == "labels" else "props=labels%7Caliases%7Cclaims" in key
        )
    )
    payload = json.loads(served[key][2])
    payload["entities"].pop(next(iter(payload["entities"])))
    served[key] = (200, {}, api_body(payload), 0.0)
    with api_server(certificate, served) as (base, requests):
        host = base.removesuffix("/repos")
        cache = tmp_path / "cache.json"
        output = tmp_path / "candidate.tsv"
        assert (
            producer.main(
                [
                    "--refresh",
                    "--out",
                    str(output),
                    "--cache-out",
                    str(cache),
                    "--query-url",
                    host + "/query",
                    "--entity-url",
                    host + "/entities",
                    "--ca-file",
                    str(certificate[0]),
                ]
            )
            == 1
        )
        assert requests
        assert not output.exists() and not cache.exists()


def test_full_utf8_preparation_precedes_destination_change(
    producer: ModuleType, tmp_path: Path
) -> None:
    document = sources()
    entity = next(iter(document["core"].values()))
    entity["labels"] = {"en": {"value": "\ud800"}}
    output = tmp_path / "candidate.tsv"
    output.write_bytes(b"previous candidate")
    with pytest.raises(UnicodeError):
        producer.build(document, output, retrieved="2026-09-26")
    assert output.read_bytes() == b"previous candidate"
    assert list(tmp_path.iterdir()) == [output]


@pytest.mark.parametrize("alias", ["source-symlink", "same-output", "ca-output"])
def test_native_resolved_input_and_snapshot_aliases(
    producer: ModuleType, tmp_path: Path, alias: str
) -> None:
    source = tmp_path / "cache.json"
    source.write_bytes((FIXTURE / "cache.json").read_bytes())
    output = tmp_path / "candidate.tsv"
    if alias == "source-symlink":
        output.symlink_to(source)
        args = ["--cache", str(source), "--out", str(output)]
    elif alias == "same-output":
        args = ["--refresh", "--out", str(output), "--cache-out", str(output)]
    else:
        args = [
            "--refresh",
            "--out",
            str(output),
            "--cache-out",
            str(source),
            "--ca-file",
            str(source),
        ]
    assert producer.main(args) == 1
    assert source.read_bytes() == (FIXTURE / "cache.json").read_bytes()
    assert output.is_symlink() if alias == "source-symlink" else not output.exists()


@pytest.mark.parametrize("size", [4096, 16384])
def test_real_atomic_write_and_close_failures_clean_temporary(tmp_path: Path, size: int) -> None:
    output = tmp_path / "candidate.tsv"
    output.write_bytes(b"previous candidate")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util,resource,signal,sys;from pathlib import Path;"
            "s=importlib.util.spec_from_file_location('producer',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "signal.signal(signal.SIGXFSZ,signal.SIG_IGN);old=resource.getrlimit(resource.RLIMIT_FSIZE);"
            "resource.setrlimit(resource.RLIMIT_FSIZE,(1024,old[1]));\n"
            'try:\n m.atomic_write(Path(sys.argv[2]),b"x"*int(sys.argv[3]))\n'
            "finally:\n resource.setrlimit(resource.RLIMIT_FSIZE,old)\n",
            str(SCRIPT),
            str(output),
            str(size),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and "File too large" in result.stderr
    assert output.read_bytes() == b"previous candidate"
    assert list(tmp_path.iterdir()) == [output]


def test_native_replace_failure_keeps_existing_directory(tmp_path: Path) -> None:
    output = tmp_path / "candidate.tsv"
    output.mkdir()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--cache", str(FIXTURE / "cache.json"), "--out", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert output.is_dir() and list(tmp_path.iterdir()) == [output]
