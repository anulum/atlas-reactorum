# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — capture-bound industrial snapshot provenance
"""Bind complete source observations to exact resources, grants and dated receipts."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from .build_dataset import table_bytes
from .capture import (
    APPROVED_TERMS_SHA256S,
    ARPAE_SERVICE,
    BASE_URLS,
    SFOE_URL,
    TERMS_URL,
    page_plan,
    page_url,
    read_captures,
)
from .contracts import (
    MAX_BYTES,
    SNAPSHOT_FIELDS,
    ImportRefused,
    object_fields,
    object_rows,
    read_json,
)
from .records import EXPECTED, project_rows
from .swiss import read_archive

GRANTS = {
    "ch-sfoe-biogas": {
        "resource_id": "6a31d549-be3e-4727-a4f8-05d7d2ab5c54",
        "resource_url": SFOE_URL,
        "license": "LicenseRef-opendata-swiss-terms-by",
        "terms_url": TERMS_URL,
    },
    "it-arpae-biogas": {
        "resource_id": "1af54eda-b778-4b21-a8dc-e4710600d25d",
        "resource_url": ARPAE_SERVICE,
        "license": "CC-BY-4.0",
        "terms_url": "https://creativecommons.org/licenses/by/4.0/",
    },
}
RECEIPT_FIELDS = {
    "name",
    "origin_url",
    "retrieved_utc",
    "bytes",
    "sha256",
    "http_status",
    "tls_verified",
}
MANIFEST_FIELDS = {
    "schema_version",
    "snapshot_sha256",
    "selected_counts",
    "raw_counts",
    "swiss_annual_rows",
    "swiss_reference_date",
    "page_size",
    "grants",
    "captures",
}
RAW_COUNTS = {"ch-sfoe-biogas": 153, "it-arpae-biogas": 330}


def receipt_date(value: object) -> str:
    """Validate an actual aware acquisition timestamp and derive its UTC date.

    Parameters
    ----------
    value : object
        Original receipt timestamp, not a generated verification timestamp.

    Returns
    -------
    str
        UTC acquisition date in ISO format.

    Raises
    ------
    ImportRefused
        Timestamp is nontext, invalid, naive or future-dated.
    """
    if not isinstance(value, str):
        raise ImportRefused("manifest acquisition timestamp is not text")
    try:
        captured = datetime.fromisoformat(value)
    except ValueError:
        raise ImportRefused("manifest acquisition timestamp is invalid") from None
    if captured.tzinfo is None or captured > datetime.now(UTC):
        raise ImportRefused("manifest acquisition timestamp is naive or in the future")
    return captured.astimezone(UTC).date().isoformat()


def check_manifest(
    manifest: dict[str, object], snapshot: bytes, observations: list[dict[str, str]]
) -> None:
    """Verify complete receipt, reviewed-count and snapshot-date bindings offline.

    Parameters
    ----------
    manifest : dict of str to object
        Frozen provenance produced after complete raw-source verification.
    snapshot : bytes
        Original canonical 28-column snapshot bytes.
    observations : list of dict
        Every decoded original snapshot cell.

    Raises
    ------
    ImportRefused
        Schema, hashes, primary resources, dates, counts or reviewed grants differ.
    """
    project_rows(observations)
    if (
        set(manifest) != MANIFEST_FIELDS
        or type(manifest.get("schema_version")) is not int
        or manifest.get("schema_version") != 1
        or manifest.get("snapshot_sha256") != hashlib.sha256(snapshot).hexdigest()
        or snapshot != table_bytes(SNAPSHOT_FIELDS, observations)
        or manifest.get("grants") != GRANTS
    ):
        raise ImportRefused("snapshot schema, byte binding or exact resource grants differ")
    for field, expected in (("selected_counts", EXPECTED), ("raw_counts", RAW_COUNTS)):
        counts = object_fields(manifest.get(field))
        if counts != expected or any(type(value) is not int for value in counts.values()):
            raise ImportRefused("manifest differs from reviewed source and selector counts")
    if type(manifest.get("swiss_annual_rows")) is not int or manifest["swiss_annual_rows"] != 974:
        raise ImportRefused("Swiss annual relations differ from the reviewed source profile")
    size = manifest.get("page_size")
    if type(size) is not int or not 0 < size <= 1000:
        raise ImportRefused("manifest page size is outside the published bounded contract")
    receipts = object_rows(manifest.get("captures"))
    by_name: dict[str, dict[str, object]] = {}
    for receipt in receipts:
        name = receipt.get("name")
        sha = receipt.get("sha256")
        count = receipt.get("bytes")
        if (
            set(receipt) != RECEIPT_FIELDS
            or not isinstance(name, str)
            or name in by_name
            or not isinstance(sha, str)
            or re.fullmatch("[0-9a-f]{64}", sha) is None
            or type(count) is not int
            or not 0 < count <= MAX_BYTES
            or type(receipt.get("http_status")) is not int
            or receipt.get("http_status") != 200
            or receipt.get("tls_verified") is not True
        ):
            raise ImportRefused("manifest receipt identity, hash, status or TLS binding differs")
        receipt_date(receipt.get("retrieved_utc"))
        by_name[name] = receipt
    pages = (
        ["ARPAE_COMPLETE.json"]
        if "ARPAE_COMPLETE.json" in by_name
        else [f"ARPAE_PAGE_{index:04d}.json" for index, _ in enumerate(range(0, 330, size))]
    )
    expected_urls = {
        **BASE_URLS,
        **{name: page_url(index * size, size) for index, name in enumerate(pages)},
    }
    if set(by_name) != set(expected_urls):
        raise ImportRefused("manifest does not contain the complete canonical resource set")
    for name, url in expected_urls.items():
        if by_name[name]["origin_url"] != url:
            raise ImportRefused("manifest receipt is not bound to its canonical publisher resource")
    if by_name["SFOE_TERMS.html"]["sha256"] not in APPROVED_TERMS_SHA256S:
        raise ImportRefused("manifest Swiss terms need a new exact-source review")
    dates = {
        "ch-sfoe-biogas": receipt_date(by_name["SFOE_ORIGINAL.csv.zip"]["retrieved_utc"]),
        "it-arpae-biogas": receipt_date(by_name[pages[-1]]["retrieved_utc"]),
    }
    if any(row["retrieved"] != dates[row["source"]] for row in observations):
        raise ImportRefused("snapshot retrieval dates do not equal original UTC acquisition dates")
    if any(
        row["source_date"] != manifest["swiss_reference_date"]
        for row in observations
        if row["source"] == "ch-sfoe-biogas"
    ):
        raise ImportRefused("Swiss snapshot reference date differs from its original metadata")


def freeze_captures(directory: Path) -> tuple[bytes, dict[str, object]]:
    """Verify complete original custody before creating a portable snapshot manifest.

    Parameters
    ----------
    directory : pathlib.Path
        Complete private original captures and their acquisition receipts.

    Returns
    -------
    tuple
        Canonical source snapshot bytes and their complete provenance manifest.

    Raises
    ------
    ImportRefused
        Any raw source, grant, receipt or reviewed source profile is invalid.
    OSError
        An original input cannot be read.
    """
    observations, receipts = read_captures(directory)
    _, size = page_plan(directory / "ARPAE_LAYER.json", directory / "ARPAE_COUNT.json")
    snapshot = table_bytes(SNAPSHOT_FIELDS, observations)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "snapshot_sha256": hashlib.sha256(snapshot).hexdigest(),
        "selected_counts": EXPECTED.copy(),
        "raw_counts": {
            "ch-sfoe-biogas": len(
                [row for row in observations if row["source"] == "ch-sfoe-biogas"]
            ),
            "it-arpae-biogas": read_json(directory / "ARPAE_COUNT.json").get("count"),
        },
        "swiss_annual_rows": len(
            read_archive(directory / "SFOE_ORIGINAL.csv.zip")["Production.csv"]
        ),
        "swiss_reference_date": next(
            row["source_date"] for row in observations if row["source"] == "ch-sfoe-biogas"
        ),
        "page_size": size,
        "grants": {source: grant.copy() for source, grant in GRANTS.items()},
        "captures": [
            {
                "name": receipt["name"],
                "origin_url": receipt.get("origin_url", receipt["url"]),
                "retrieved_utc": receipt["retrieved_utc"],
                "bytes": receipt["bytes"],
                "sha256": receipt["sha256"],
                "http_status": receipt["http_status"],
                "tls_verified": receipt["tls_verified"],
            }
            for receipt in sorted(receipts, key=lambda record: str(record["name"]))
        ],
    }
    check_manifest(manifest, snapshot, observations)
    return snapshot, manifest
