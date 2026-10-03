# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — industrial facility producer conformance

"""Build the complete six-source industrial layer through public and native APIs."""

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

from ._catalogue_inputs import ROOT, run_cli
from .conftest import load_module
from .test_public_reactor_repository_build import api_body, api_server
from .test_public_reactor_repository_build import certificate as certificate

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities"
SCRIPT = DIRECTORY / "build_industrial_facilities.py"
ACCEPTED = DIRECTORY / "industrial_facilities.tsv"
FIXTURE = ROOT / "tests/data/industrial_base"
NAMES = ("EEA", "Mixed", "Cattle", "Poultry", "Swine", "Dairy")


@pytest.fixture
def producer() -> ModuleType:
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_producer")


def sources() -> dict[str, Any]:
    """Read every captured original source cell and its independent count."""
    return {
        "schema_version": "1.0.0",
        "captured_at": "2026-09-30",
        "sources": {name: json.loads((FIXTURE / (name + ".json")).read_bytes()) for name in NAMES},
    }


def source_file(tmp_path: Path, document: object | None = None) -> Path:
    """Save a complete source copy with an explicit corruption when requested."""
    path = tmp_path / "source.json"
    path.write_text(json.dumps(sources() if document is None else document), encoding="utf-8")
    return path


def service_routes(
    producer: ModuleType,
    document: dict[str, Any],
    page_size: int = 1000,
) -> dict[str, tuple[int, dict[str, str], bytes, float]]:
    """Serve genuine source/count payloads at the exact public query URLs."""
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {}
    for name, source in document["sources"].items():
        path = "/eea/query" if name == "EEA" else f"/epa/{name}/FeatureServer/0/query"
        where = producer.EEA_WHERE if name == "EEA" else "1=1"
        count_query = urllib.parse.urlencode(
            {"f": "json", "where": where, "returnCountOnly": "true"}
        )
        routes[path + "?" + count_query] = (200, {}, api_body({"count": source["count"]}), 0.0)
        for offset in range(0, source["count"], page_size):
            query = urllib.parse.urlencode(
                {
                    "f": "json",
                    "where": where,
                    "outFields": producer.EEA_FIELDS if name == "EEA" else producer.EPA_FIELDS,
                    "returnGeometry": "false",
                    "orderByFields": "OBJECTID ASC",
                    "resultOffset": str(offset),
                    "resultRecordCount": str(page_size),
                }
            )
            features = [
                {"attributes": record} for record in source["records"][offset : offset + page_size]
            ]
            routes[path + "?" + query] = (
                200,
                {},
                api_body(
                    {
                        "features": features,
                        "exceededTransferLimit": offset + len(features) < source["count"],
                    }
                ),
                0.0,
            )
    return routes


def test_complete_sources_reproduce_every_historical_byte(
    producer: ModuleType, tmp_path: Path
) -> None:
    document = sources()
    assert sum(row["count"] for row in document["sources"].values()) == 6550
    metadata = json.loads((FIXTURE / "SOURCE.json").read_bytes())
    for source in metadata["sources"]:
        assert (
            hashlib.sha256((FIXTURE / source["fixture"]).read_bytes()).hexdigest()
            == source["fixture_sha256"]
        )
    output = tmp_path / "candidate.tsv"
    producer.build(document, output, retrieved="2026-09-27")
    assert output.read_bytes() == ACCEPTED.read_bytes()


@pytest.mark.parametrize("optimize", [False, True])
def test_native_offline_reproduction_and_real_validator(tmp_path: Path, optimize: bool) -> None:
    path = source_file(tmp_path)
    output = tmp_path / "candidate.tsv"
    result = run_cli(
        SCRIPT,
        "--source",
        str(path),
        "--output",
        str(output),
        "--date",
        "2026-09-27",
        optimize=optimize,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == ACCEPTED.read_bytes()
    validation = run_cli(DIRECTORY / "validate.py", "--dataset", str(output), optimize=optimize)
    assert validation.returncode == 0, validation.stdout + validation.stderr


@pytest.mark.parametrize(
    "case", ["default-date", "bad-json", "bad-utf8", "missing-source", "bad-date"]
)
def test_native_source_and_date_handling(tmp_path: Path, case: str) -> None:
    path = source_file(tmp_path)
    if case == "bad-json":
        path.write_bytes(b"{")
    elif case == "bad-utf8":
        path.write_bytes(b"\xff")
    elif case == "missing-source":
        path.unlink()
    output = tmp_path / "candidate.tsv"
    result = run_cli(
        SCRIPT,
        "--source",
        str(path),
        "--output",
        str(output),
        *(["--date", "20260927"] if case == "bad-date" else []),
    )
    assert "Traceback" not in result.stderr
    if case == "default-date":
        assert result.returncode == 0
        rows = list(csv.DictReader(io.StringIO(output.read_text()), delimiter="\t"))
        assert len(rows) == 6550 and {row["retrieved"] for row in rows} == {"2026-09-30"}
    else:
        assert result.returncode == 1 and not output.exists()


@pytest.mark.parametrize(
    "case",
    [
        "scalar",
        "schema",
        "source-map",
        "capture",
        "capture-compact",
        "content",
        "count",
        "boolean-count",
        "records",
        "empty",
    ],
)
def test_corrupt_source_envelope_refuses_every_output(
    producer: ModuleType, tmp_path: Path, case: str
) -> None:
    document: Any = sources()
    if case == "scalar":
        document = 1
    elif case == "schema":
        document["schema_version"] = "2.0.0"
    elif case == "source-map":
        document["sources"].pop("Mixed")
    elif case == "capture":
        document["captured_at"] = None
    elif case == "capture-compact":
        document["captured_at"] = "20260930"
    elif case == "content":
        document["sources"]["EEA"] = None
    elif case == "count":
        document["sources"]["EEA"]["count"] -= 1
    elif case == "boolean-count":
        document["sources"]["EEA"]["count"] = True
    elif case == "records":
        document["sources"]["EEA"]["records"] = None
    else:
        for content in document["sources"].values():
            content.update(count=0, records=[])
    with pytest.raises((ValueError, TypeError)):
        producer.build(document, tmp_path / "candidate", retrieved="2026-09-27")
    assert not (tmp_path / "candidate").exists()


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("EEA", "OBJECTID", 0),
        ("EEA", "OBJECTID", True),
        ("EEA", "siteName", {}),
        ("EEA", "y_4258", None),
        ("EEA", "x_4258", ""),
        ("EEA", "y_4258", 91),
        ("EEA", "x_4258", -181),
        ("EEA", "x_4258", float("nan")),
        ("EEA", "x_4258", float("inf")),
        ("EEA", "y_4258", "not numeric"),
        ("EEA", "Site_reporting_year", 2023),
        ("EEA", "eprtr_sectors", "POWER"),
        ("EEA", "countryCode", ""),
        ("EEA", "InspireSiteId", ""),
        ("EEA", "InspireSiteId", "!!!"),
        ("Mixed", "Project_Na", ""),
        ("Mixed", "Population", "NaN"),
        ("Mixed", "Biogas_Gen", float("inf")),
        ("Mixed", "LATITUDE__", 91),
    ],
)
def test_corrupt_real_source_cells_refuse_without_writes(
    producer: ModuleType,
    tmp_path: Path,
    name: str,
    field: str,
    value: object,
) -> None:
    document = sources()
    document["sources"][name]["records"][0][field] = value
    with pytest.raises((ValueError, RuntimeError)):
        producer.build(document, tmp_path / "candidate", retrieved="2026-09-27")
    assert not (tmp_path / "candidate").exists()


@pytest.mark.parametrize(
    "case", ["record-scalar", "field-missing", "object-duplicate", "site-duplicate", "site-name"]
)
def test_source_identity_and_schema_integrity(
    producer: ModuleType, tmp_path: Path, case: str
) -> None:
    document = sources()
    records = document["sources"]["EEA"]["records"]
    if case == "record-scalar":
        records[0] = None
    elif case == "field-missing":
        records[0].pop("pollutants")
    elif case == "object-duplicate":
        records[1]["OBJECTID"] = records[0]["OBJECTID"]
    elif case == "site-duplicate":
        records[1]["InspireSiteId"] = records[0]["InspireSiteId"]
    else:
        records[0].update(siteName=None, facilityNames=None)
    with pytest.raises(ValueError):
        producer.build(document, tmp_path / "candidate", retrieved="2026-09-27")
    assert not (tmp_path / "candidate").exists()


def test_unknown_optional_observations_and_source_ranges_are_preserved(
    producer: ModuleType, tmp_path: Path
) -> None:
    document = sources()
    eea = document["sources"]["EEA"]["records"][0]
    eea.update(
        siteName=None, countryCode="ZZ", eea_activities=None, activity_details=None, pollutants=None
    )
    epa = document["sources"]["Mixed"]["records"][0]
    epa.update(
        Project_Ty=None,
        Animal_T_1=None,
        Co_Digesti=None,
        Biogas_End=None,
        Total_Emis=None,
        Population="1,234",
        Biogas_Gen="10-20",
        Electricit=None,
    )
    output = tmp_path / "candidate"
    producer.build(document, output, retrieved="2026-09-27")
    rows = list(csv.DictReader(io.StringIO(output.read_text()), delimiter="\t"))
    original_eea = next(row for row in rows if row["country"] == "ZZ")
    assert original_eea["facility_name"] == eea["facilityNames"].strip()
    assert (
        original_eea["reactor_type_if_explicit"] == "" and original_eea["process_or_activity"] == ""
    )
    changed = next(row for row in rows if row["facility_name"] == epa["Project_Na"].strip())
    assert (
        changed["capacity"]
        == "population feeding digester: 1234 animals | estimated biogas: 10-20 ft3/day"
    )
    assert changed["pollutant_or_product_context"] == "animal/feedstock class: Mixed"
    assert changed["process_or_activity"] == "anaerobic digestion"


@pytest.mark.parametrize(
    "options",
    [
        [],
        ["--refresh"],
        ["--snapshot-out", "snapshot.json"],
        ["--ca-file", "missing.pem"],
        ["--eea-url", "https://example.org"],
        ["--epa-base", "https://example.org"],
    ],
)
def test_inconsistent_native_options_refuse_without_outputs(
    tmp_path: Path, options: list[str]
) -> None:
    result = run_cli(SCRIPT, "--output", str(tmp_path / "candidate"), *options)
    assert result.returncode == 1 and not (tmp_path / "candidate").exists()


def test_real_output_alias_and_atomic_failures(producer: ModuleType, tmp_path: Path) -> None:
    before = ACCEPTED.read_bytes()
    link = tmp_path / "accepted"
    link.symlink_to(ACCEPTED)
    with pytest.raises(ValueError):
        producer.build(sources(), link, retrieved="2026-09-27")
    target = tmp_path / "input"
    with pytest.raises(ValueError):
        producer.build(sources(), target, retrieved="2026-09-27", inputs=(target,))
    target.mkdir()
    with pytest.raises(OSError):
        producer.build(sources(), target, retrieved="2026-09-27")
    assert {path.name for path in tmp_path.iterdir()} == {"accepted", "input"}
    assert ACCEPTED.read_bytes() == before


@pytest.mark.parametrize("size", [4096, 16384])
def test_real_buffered_and_direct_write_failures_clean_only_owned_temporaries(
    tmp_path: Path, size: int
) -> None:
    target = tmp_path / "candidate"
    target.write_bytes(b"previous")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util,resource,signal,sys;from pathlib import Path;"
            "s=importlib.util.spec_from_file_location('p',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "signal.signal(signal.SIGXFSZ,signal.SIG_IGN);old=resource.getrlimit(resource.RLIMIT_FSIZE);"
            "resource.setrlimit(resource.RLIMIT_FSIZE,(1024,old[1]));\n"
            "try:\n m.atomic_write(Path(sys.argv[2]),b'x'*int(sys.argv[3]))\n"
            "finally:\n resource.setrlimit(resource.RLIMIT_FSIZE,old)\n",
            str(SCRIPT),
            str(target),
            str(size),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and "File too large" in result.stderr
    assert list(tmp_path.iterdir()) == [target] and target.read_bytes() == b"previous"


def test_complete_trusted_tls_native_refresh_and_paginated_sources(
    producer: ModuleType,
    certificate: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    document = sources()
    routes = service_routes(producer, document)
    with api_server(certificate, routes) as (base, requests):
        base = base.removesuffix("/repos")
        found = producer.query_all(
            base + "/eea", producer.EEA_WHERE, producer.EEA_FIELDS, ca_file=certificate[0]
        )
        assert found == document["sources"]["EEA"] and len(requests) == 8
        output, snapshot = tmp_path / "candidate", tmp_path / "snapshot"
        result = run_cli(
            SCRIPT,
            "--refresh",
            "--eea-url",
            base + "/eea",
            "--epa-base",
            base + "/epa",
            "--ca-file",
            str(certificate[0]),
            "--snapshot-out",
            str(snapshot),
            "--output",
            str(output),
            "--date",
            "2026-09-27",
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_bytes() == ACCEPTED.read_bytes()
        captured = json.loads(snapshot.read_bytes())
        assert (
            captured["sources"] == document["sources"]
            and captured["captured_at"] == date.today().isoformat()
        )
        assert len(requests) == 26


@pytest.mark.parametrize(
    "case",
    [
        "count-scalar",
        "count-negative",
        "count-bool",
        "count-small",
        "page-limit",
        "feature-list",
        "empty-page",
        "large-page",
        "transfer-flag",
        "feature-scalar",
        "attributes",
        "non-object",
        "api-error",
        "body-limit",
        "201",
        "404",
        "untrusted",
        "stall",
        "invalid-json",
    ],
)
def test_real_tls_source_count_page_and_transport_refusals(
    producer: ModuleType,
    certificate: tuple[Path, Path],
    case: str,
) -> None:
    document = sources()
    routes = service_routes(producer, document)
    count_path = next(
        path for path in routes if path.startswith("/eea/") and "returnCountOnly" in path
    )
    page_path = next(
        path for path in routes if path.startswith("/eea/") and "resultOffset=0" in path
    )
    options: dict[str, Any] = {"ca_file": certificate[0], "timeout": 0.5}
    if case in {"count-scalar", "count-negative", "count-bool", "count-small"}:
        count = {
            "count-scalar": "6150",
            "count-negative": -1,
            "count-bool": True,
            "count-small": 999,
        }[case]
        routes[count_path] = (200, {}, api_body({"count": count}), 0.0)
    elif case == "page-limit":
        options["max_pages"] = 1
    elif case in {
        "feature-list",
        "empty-page",
        "large-page",
        "transfer-flag",
        "feature-scalar",
        "attributes",
    }:
        page = json.loads(routes[page_path][2])
        if case == "feature-list":
            page["features"] = {}
        elif case == "empty-page":
            page["features"] = []
        elif case == "large-page":
            page["features"].append(page["features"][0])
        elif case == "transfer-flag":
            page["exceededTransferLimit"] = "false"
        elif case == "feature-scalar":
            page["features"][0] = 1
        else:
            page["features"][0]["attributes"] = None
        routes[page_path] = (200, {}, api_body(page), 0.0)
    elif case in {"non-object", "api-error", "invalid-json"}:
        body = {"non-object": b"[]", "api-error": b'{"error":{"code":500}}', "invalid-json": b"{"}[
            case
        ]
        routes[count_path] = (200, {}, body, 0.0)
    elif case == "body-limit":
        options["max_bytes"] = 1
    elif case in {"201", "404"}:
        routes[count_path] = (int(case), {}, routes[count_path][2], 0.0)
    elif case == "untrusted":
        options["ca_file"] = None
    else:
        routes[count_path] = (200, {}, routes[count_path][2], 0.15)
        options["timeout"] = 0.03
    with api_server(certificate, routes) as (base, requests):
        with pytest.raises((OSError, ValueError)):
            producer.query_all(
                base.removesuffix("/repos") + "/eea",
                producer.EEA_WHERE,
                producer.EEA_FIELDS,
                **options,
            )
        assert all(path.startswith("/eea/query?") for path in requests)


@pytest.mark.parametrize(("size", "max_pages"), [(1000, 7), (1000, 8)])
def test_paginated_count_completion_at_last_permitted_page(
    producer: ModuleType,
    certificate: tuple[Path, Path],
    size: int,
    max_pages: int,
) -> None:
    routes = service_routes(producer, sources(), size)
    with api_server(certificate, routes) as (base, _requests):
        found = producer.query_all(
            base.removesuffix("/repos") + "/eea",
            producer.EEA_WHERE,
            producer.EEA_FIELDS,
            page_size=size,
            max_pages=max_pages,
            ca_file=certificate[0],
        )
        assert found == sources()["sources"]["EEA"]


def test_empty_real_selection_and_query_parameter_joining(
    producer: ModuleType,
    certificate: tuple[Path, Path],
) -> None:
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {
        "/eea/query?f=json&where=1%3D0&returnCountOnly=true": (200, {}, b'{"count":0}', 0.0),
        "/eea?mirror=yes&f=json": (200, {}, api_body(sources()["sources"]["EEA"]), 0.0),
    }
    with api_server(certificate, routes) as (base, requests):
        base = base.removesuffix("/repos")
        assert producer.query_all(
            base + "/eea", "1=0", producer.EEA_FIELDS, ca_file=certificate[0]
        ) == {"count": 0, "records": []}
        assert (
            producer.request_json(base + "/eea?mirror=yes", {"f": "json"}, ca_file=certificate[0])
            == sources()["sources"]["EEA"]
        )
        assert len(requests) == 2


@pytest.mark.parametrize("target", ["accepted", "downgrade", "credentials", "loop"])
def test_real_redirect_destination_validation(
    producer: ModuleType,
    certificate: tuple[Path, Path],
    target: str,
) -> None:
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {}
    with api_server(certificate, routes) as (base, requests):
        destinations = {
            "accepted": base + "?final=1",
            "downgrade": base.replace("https:", "http:"),
            "credentials": base.replace("https://", "https://user@"),
            "loop": base + "?f=json",
        }
        routes["/repos?f=json"] = (302, {"Location": destinations[target]}, b"", 0.0)
        routes["/repos?final=1"] = (200, {}, api_body(sources()["sources"]["Mixed"]), 0.0)
        if target == "accepted":
            assert (
                producer.request_json(base, {"f": "json"}, ca_file=certificate[0])
                == sources()["sources"]["Mixed"]
            )
            assert requests == ["/repos?f=json", "/repos?final=1"]
        else:
            with pytest.raises((ValueError, OSError)):
                producer.request_json(base, {"f": "json"}, ca_file=certificate[0])
            assert set(requests) == {"/repos?f=json"}


@pytest.mark.parametrize(
    "options",
    [
        {"timeout": 0},
        {"timeout": float("inf")},
        {"timeout": float("nan")},
        {"max_bytes": 0},
        {"page_size": 0},
        {"max_pages": 0},
    ],
)
def test_invalid_request_limits_refuse_before_network(
    producer: ModuleType, options: dict[str, int | float]
) -> None:
    with pytest.raises(ValueError):
        producer.query_all(producer.EEA_LAYER, producer.EEA_WHERE, producer.EEA_FIELDS, **options)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost",
        "https:///data",
        "https://user@localhost",
        "https://localhost:0",
        "https://localhost:invalid",
        "https://localhost/data#part",
        "https://localhost/da ta",
    ],
)
def test_invalid_source_urls_refuse_before_network(producer: ModuleType, url: str) -> None:
    with pytest.raises(ValueError):
        producer.request_json(url, {"f": "json"})


@pytest.mark.parametrize(
    "case",
    [
        "output",
        "snapshot",
        "ca",
        "offline-source",
        "refresh-source",
        "bad-date",
        "unicode",
        "invalid-site",
    ],
)
def test_native_refresh_preparation_and_path_errors_never_write(
    producer: ModuleType,
    certificate: tuple[Path, Path],
    tmp_path: Path,
    case: str,
) -> None:
    document = sources()
    if case == "unicode":
        document["sources"]["EEA"]["records"][0]["siteName"] = "\ud800"
    elif case == "invalid-site":
        document["sources"]["EEA"]["records"][0]["InspireSiteId"] = ""
    routes = service_routes(producer, document)
    with api_server(certificate, routes) as (base, _requests):
        base = base.removesuffix("/repos")
        output = tmp_path / "candidate"
        snapshot = tmp_path / "snapshot"
        options = [
            "--refresh",
            "--eea-url",
            base + "/eea",
            "--epa-base",
            base + "/epa",
            "--ca-file",
            str(certificate[0]),
        ]
        if case == "output":
            output = ACCEPTED
        elif case == "snapshot":
            snapshot = ACCEPTED
        elif case == "ca":
            snapshot = certificate[0]
        elif case == "offline-source":
            source = source_file(tmp_path)
            output = source
            options = []
            options.extend(["--source", str(source)])
        elif case == "refresh-source":
            options.extend(["--source", str(source_file(tmp_path))])
        elif case == "bad-date":
            options.extend(["--date", "invalid"])
        before = ACCEPTED.read_bytes()
        cert_before = certificate[0].read_bytes()
        result = run_cli(SCRIPT, *options, "--snapshot-out", str(snapshot), "--output", str(output))
        assert result.returncode == 1 and "Traceback" not in result.stderr
        assert ACCEPTED.read_bytes() == before and certificate[0].read_bytes() == cert_before
        assert not (tmp_path / "candidate").exists() and not (tmp_path / "snapshot").exists()
