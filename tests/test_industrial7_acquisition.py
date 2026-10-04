# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — real trusted TLS source acquisition
"""Exercise complete original sources, pagination, transport guards and partial custody."""

from __future__ import annotations

import hashlib
import json
import ssl
from pathlib import Path

import pytest

from ._industrial7_sources import (
    ACQUISITION,
    CAPTURE,
    ROOT,
    _prepared_custody,
    copy_custody,
    receipt_change,
    run_cli,
    tls_source,
)
from ._industrial7_sources import source_custody as source_custody


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/data",
        "https:///missing",
        "https://user@localhost/data",
        "https://user:password@localhost/data",
        "https://localhost:0/",
        "https://localhost:65536/",
        "https://localhost:invalid/",
        "https://[bad/",
        "https://localhost/data#fragment",
        "https://localhost/white space",
    ],
)
def test_invalid_source_url_before_network(url: str) -> None:
    """Reject malformed acquisition URLs before opening a transport connection.

    Parameters
    ----------
    url : str
        Anonymous-HTTPS boundary violation under test.
    """
    with pytest.raises(ValueError, match="source URL"):
        ACQUISITION.download(url)


@pytest.mark.parametrize(
    "options",
    [
        {"timeout": 0},
        {"timeout": float("nan")},
        {"timeout": -1},
        {"deadline_seconds": 0},
        {"deadline_seconds": float("nan")},
        {"max_bytes": 0},
        {"max_bytes": True},
        {"max_bytes": 1.5},
    ],
)
def test_positive_finite_source_limits(options: dict[str, object]) -> None:
    """Reject invalid resource limits before fetching any publisher bytes.

    Parameters
    ----------
    options : dict of str to object
        Invalid socket timeout, elapsed deadline or maximum response size.
    """
    with pytest.raises(ValueError, match="source limits"):
        ACQUISITION.download(CAPTURE.SFOE_URL, **options)


def test_actual_source_bytes_root_and_query_targets(source_custody: Path, tmp_path: Path) -> None:
    """Preserve complete archive bytes and require a trusted TLS certificate.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    """
    expected = (source_custody / "SFOE_ORIGINAL.csv.zip").read_bytes()
    with tls_source(tmp_path, source_custody) as (base, ca):
        assert ACQUISITION.download(base, ca_file=ca) == expected
        assert (
            ACQUISITION.download(base + "/files/SFOE_ORIGINAL.csv.zip?probe=1", ca_file=ca)
            == expected
        )
        with pytest.raises(ssl.SSLCertVerificationError):
            ACQUISITION.download(base + "/files/SFOE_ORIGINAL.csv.zip")


@pytest.mark.parametrize("status", [204, 301, 302, 307, 308, 404, 503])
def test_real_http_status_refusal_without_following(
    source_custody: Path, tmp_path: Path, status: int
) -> None:
    """Refuse redirect and error responses rather than treating them as source data.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    status : int
        Actual HTTP status returned by the controlled TLS server.
    """
    with tls_source(tmp_path, source_custody) as (base, ca):
        with pytest.raises(ValueError, match="HTTP 200"):
            ACQUISITION.download(base + f"/status/{status}", ca_file=ca)


def test_actual_byte_limit_and_checked_deadline(source_custody: Path, tmp_path: Path) -> None:
    """Stop genuine TLS reads that exceed byte or elapsed-time bounds.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    """
    with tls_source(tmp_path, source_custody) as (base, ca):
        with pytest.raises(ValueError, match="byte limit"):
            ACQUISITION.download(base + "/files/SFOE_ORIGINAL.csv.zip", ca_file=ca, max_bytes=100)
        with pytest.raises(ValueError, match="deadline"):
            ACQUISITION.download(base + "/slow", ca_file=ca, deadline_seconds=0.02)


@pytest.mark.parametrize("kind", ["repository", "existing_directory", "existing_file", "symlink"])
def test_new_external_custody_guards(source_custody: Path, tmp_path: Path, kind: str) -> None:
    """Preserve existing owner paths and refuse capture targets inside the checkout.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    kind : str
        Repository path, existing directory, existing file or symlink refusal.
    """
    target = tmp_path / "output"
    if kind == "repository":
        target = ROOT / "tests/data/industrial_round7/refused-capture"
    elif kind == "existing_directory":
        target.mkdir()
    elif kind == "existing_file":
        target.write_text("preserve existing owner bytes")
    else:
        target.symlink_to(source_custody, target_is_directory=True)
    with pytest.raises(ValueError, match="external and previously absent"):
        ACQUISITION.acquire(target)


@pytest.mark.parametrize(
    "base",
    [
        "http://untrusted.invalid",
        "https://host/path?query=1",
        "https://user@host",
        "https://host/path#fragment",
        "https://host:invalid",
    ],
)
def test_mirror_boundaries_before_custody_creation(tmp_path: Path, base: str) -> None:
    """Refuse an invalid explicit mirror without creating its capture destination.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    base : str
        Mirror URL violating the HTTPS, query, credentials or fragment boundary.
    """
    target = tmp_path / "output"
    with pytest.raises(ValueError):
        ACQUISITION.acquire(target, mirror_base=base)
    assert not target.exists()


def test_complete_actual_tls_acquisition_and_source_parity(
    source_custody: Path, tmp_path: Path
) -> None:
    """Bind complete mirrored source observations to real receipt hashes and URLs.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    """
    target = tmp_path / "capture"
    with tls_source(tmp_path, source_custody) as (base, ca):
        rows, receipts = ACQUISITION.acquire(target, mirror_base=base + "/files", ca_file=ca)
    original, _ = CAPTURE.read_captures(source_custody)
    assert len(rows) == 421 and len(receipts) == 8
    for actual, expected in zip(rows, original, strict=True):
        assert {key: value for key, value in actual.items() if key != "retrieved"} == {
            key: value for key, value in expected.items() if key != "retrieved"
        }
    for receipt in receipts:
        body = (target / receipt["name"]).read_bytes()
        assert receipt["tls_verified"] is True and receipt["http_status"] == 200
        assert receipt["bytes"] == len(body)
        assert receipt["sha256"] == hashlib.sha256(body).hexdigest()
        assert receipt["url"].startswith(base + "/files/")
        assert receipt["origin_url"].startswith("https://")


def test_complete_real_rows_across_publisher_page_boundary(
    source_custody: Path, tmp_path: Path
) -> None:
    """Preserve every original feature when the publisher requires two pages.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    """
    layer = json.loads((source_custody / "ARPAE_LAYER.json").read_text())
    layer["maxRecordCount"] = 165
    page = json.loads((source_custody / "ARPAE_COMPLETE.json").read_text())
    first, last = dict(page), dict(page)
    first["features"], last["features"] = page["features"][:165], page["features"][165:]
    first["exceededTransferLimit"], last["exceededTransferLimit"] = True, False
    overrides = {
        "ARPAE_LAYER.json": json.dumps(layer).encode(),
        "ARPAE_PAGE_0000.json": json.dumps(first).encode(),
        "ARPAE_PAGE_0001.json": json.dumps(last).encode(),
    }
    with tls_source(tmp_path, source_custody, overrides) as (base, ca):
        rows, receipts = ACQUISITION.acquire(
            tmp_path / "paged", mirror_base=base + "/files", ca_file=ca
        )
    assert len(rows) == 421 and len(receipts) == 9
    assert (tmp_path / "paged/ARPAE_PAGE_0001.json").is_file()


@pytest.mark.parametrize("failure", ["count", "page_limit", "partial_transport", "changed_terms"])
def test_failed_acquisition_retains_real_partial_custody(
    source_custody: Path, tmp_path: Path, failure: str
) -> None:
    """Retain acquired archive bytes and receipts when later source checks fail.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    failure : str
        Invalid count, page limit, source document or unreviewed terms mutation.
    """
    overrides: dict[str, bytes] = {}
    if failure == "count":
        value = json.loads((source_custody / "ARPAE_COUNT.json").read_text())
        value["count"] = False
        overrides["ARPAE_COUNT.json"] = json.dumps(value).encode()
    elif failure == "page_limit":
        value = json.loads((source_custody / "ARPAE_LAYER.json").read_text())
        value["maxRecordCount"] = 0
        overrides["ARPAE_LAYER.json"] = json.dumps(value).encode()
    elif failure == "partial_transport":
        overrides["ARPAE_METADATA.json"] = b"invalid native JSON"
    else:
        overrides["SFOE_TERMS.html"] = (source_custody / "SFOE_TERMS.html").read_bytes() + b" "
    target = tmp_path / "failed"
    with tls_source(tmp_path, source_custody, overrides) as (base, ca):
        with pytest.raises(ValueError):
            ACQUISITION.acquire(target, mirror_base=base + "/files", ca_file=ca)
    assert (target / "SFOE_ORIGINAL.csv.zip").read_bytes() == (
        source_custody / "SFOE_ORIGINAL.csv.zip"
    ).read_bytes()
    assert (target / "SFOE_ORIGINAL.csv.zip.receipt.json").is_file()


@pytest.mark.parametrize("optimize", [False, True])
def test_real_native_acquisition_cli(source_custody: Path, tmp_path: Path, optimize: bool) -> None:
    """Require the public acquisition CLI to succeed and refuse a repeated destination.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete real publisher captures with original acquisition receipts.
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    optimize : bool
        Run the native interpreter normally or with optimization enabled.
    """
    target = tmp_path / "native"
    with tls_source(tmp_path, source_custody) as (base, ca):
        success = run_cli(
            "acquisition",
            target,
            "--mirror-base",
            base + "/files",
            "--ca-file",
            str(ca),
            optimize=optimize,
        )
    assert success.returncode == 0, success.stdout + success.stderr
    assert json.loads(success.stdout)["observations"] == 421
    failure = run_cli("acquisition", target, optimize=optimize)
    assert failure.returncode == 1 and "ACQUISITION FAILED" in failure.stdout
    assert "Traceback" not in failure.stderr


def test_live_original_source_acquisition(tmp_path: Path) -> None:
    """Require complete current publisher acquisition with canonical origin receipts.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owned external directory for TLS keys, capture files and negative copies.
    """
    target = tmp_path / "direct"
    rows, receipts = ACQUISITION.acquire(target)
    assert len(rows) == 421 and len(receipts) == 8
    for receipt in receipts:
        assert receipt["url"] == receipt["origin_url"]


@pytest.mark.parametrize("kind", ["valid", "changed_terms", "missing_receipt"])
def test_retained_session_custody_preserves_original_validation(
    source_custody: Path, tmp_path: Path, kind: str
) -> None:
    """Revisit genuine retained sources without replacing original failure evidence.

    Parameters
    ----------
    source_custody : pathlib.Path
        Complete original publisher bytes and acquisition receipts.
    tmp_path : pathlib.Path
        External directory for the isolated retained session capture.
    kind : str
        Positive retained input, altered terms or an incomplete receipt set.
    """
    directory = tmp_path / "atlas-industrial7-native-source" / "capture"
    directory.parent.mkdir()
    copy_custody(directory, source_custody)
    if kind == "changed_terms":
        path = directory / "SFOE_TERMS.html"
        original = path.read_bytes()
        changed = original.replace(
            b"You <strong>may</strong> use this dataset for commercial purposes.",
            b"You <strong>may not</strong> use this dataset for commercial purposes.",
        )
        assert changed != original
        path.write_bytes(changed)
        receipt_change(directory, path.name, "bytes", len(changed))
        receipt_change(directory, path.name, "sha256", hashlib.sha256(changed).hexdigest())
    elif kind == "missing_receipt":
        (directory / "SFOE_METADATA.json.receipt.json").unlink()
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    for _ in range(2):
        if kind == "valid":
            assert _prepared_custody(tmp_path, None) == directory
            assert len(CAPTURE.read_captures(directory)[0]) == 421
        elif kind == "changed_terms":
            with pytest.raises(ValueError, match="Swiss terms capture differs"):
                _prepared_custody(tmp_path, None)
        else:
            with pytest.raises(ValueError, match="source capture must be a bounded regular file"):
                _prepared_custody(tmp_path, None)
        assert {path.name: path.read_bytes() for path in directory.iterdir()} == before
