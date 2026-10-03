# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — verified source capture custody
"""Verify dated original source custody and the exact upstream rights binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import SplitResult, urlencode, urlsplit

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .contracts import HERE, MAX_BYTES, ImportRefused, object_fields, object_rows, read_json
from .italian import read_italian
from .swiss import read_swiss

REPOSITORY = HERE.parents[3]
SFOE_URL = "https://data.geo.admin.ch/ch.bfe.biogasanlagen/biogasanlagen/biogasanlagen_2056.csv.zip"
ARPAE_SERVICE = (
    "https://servizi-gis.arpae.it/server/rest/services/Geoportal/ENERGIAImpianti/MapServer"
)
TERMS_URL = "https://opendata.swiss/terms-of-use#terms_by"
APPROVED_TERMS_SHA256 = "da4b7868e59693e5ac09ba5e3eed66acfb21a022ffc45fc3f38d29fdfa3ddf15"
# Reviewed versions differ solely in the unrelated footer dataset counter.
APPROVED_TERMS_SHA256S = frozenset(
    {
        APPROVED_TERMS_SHA256,
        "39ce38674a42d807593e8972d5291e6c8c9074a7297264c22da3f3ad4f80fcc6",
    }
)
BASE_URLS = {
    "SFOE_METADATA.json": "https://ckan.opendata.swiss/api/3/action/package_show?id=biogasanlagen",
    "SFOE_ORIGINAL.csv.zip": SFOE_URL,
    "SFOE_TERMS.html": "https://opendata.swiss/en/terms-of-use",
    "ARPAE_METADATA.json": "https://dati.arpae.it/api/3/action/package_show?id=arpa_ene_impianti_biomasse_biogas",
    "ARPAE_LAYER.json": ARPAE_SERVICE + "/0?f=pjson",
    "ARPAE_COUNT.json": ARPAE_SERVICE + "/0/query?where=1%3D1&returnCountOnly=true&f=json",
    "ARPAE_IDS.json": ARPAE_SERVICE + "/0/query?where=1%3D1&returnIdsOnly=true&f=json",
}


def checked_url(url: str) -> SplitResult:
    """Require anonymous HTTPS for original resources and explicit trusted mirrors.

    Parameters
    ----------
    url : str
        Actual resource or mirror URL.

    Returns
    -------
    urllib.parse.SplitResult
        Parsed URL after port, credentials, whitespace and fragment checks.

    Raises
    ------
    ImportRefused
        The URL is malformed or does not meet the acquisition boundary.
    """
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise ImportRefused("source URL is malformed") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port == 0
        or parsed.fragment
        or any(character.isspace() for character in url)
    ):
        raise ImportRefused("source URL must be anonymous HTTPS without a fragment")
    return parsed


def page_plan(layer: Path, count: Path) -> tuple[int, int]:
    """Check native whole-source count and page limit before planning complete capture.

    Parameters
    ----------
    layer, count : pathlib.Path
        Full native metadata and independently queried count captures.

    Returns
    -------
    tuple of int
        Whole-source count and bounded page size, at most 1,000 records.

    Raises
    ------
    ImportRefused
        The count or publisher limit is not a bounded positive integer.
    """
    total = read_json(count).get("count")
    limit = read_json(layer).get("maxRecordCount")
    if (
        type(total) is not int
        or not 0 < total <= 100_000
        or type(limit) is not int
        or not 0 < limit <= 100_000
    ):
        raise ImportRefused("Italian acquisition count or page limit is outside its bound")
    return total, min(limit, 1000)


def page_url(offset: int, size: int) -> str:
    """Build the canonical complete-field WGS84 query for a planned publisher page.

    Parameters
    ----------
    offset, size : int
        Nonnegative offset and positive size produced by the native page plan.

    Returns
    -------
    str
        Publisher query retaining deterministic OBJECTID order.
    """
    query = urlencode(
        {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "orderByFields": "OBJECTID",
            "resultOffset": offset,
            "resultRecordCount": size,
            "f": "json",
        }
    )
    return ARPAE_SERVICE + "/0/query?" + query


def verified_receipt(directory: Path, name: str, *, expected_url: str) -> dict[str, object]:
    """Bind one complete original file to its actual dated retrieval receipt.

    Parameters
    ----------
    directory : pathlib.Path
        Original capture custody.
    name : str
        Fixed producer resource name.
    expected_url : str
        Exact canonical publisher URL for this resource or planned page.

    Returns
    -------
    dict
        Verified original receipt members.

    Raises
    ------
    ImportRefused
        Hash, size, date, name, original URL or positive TLS/status evidence differs.
    """
    if Path(name).name != name:
        raise ImportRefused("source capture name must be a single resource filename")
    path = directory / name
    receipt = read_json(directory / (name + ".receipt.json"))
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ImportRefused("original source capture is not a bounded regular file")
    body = path.read_bytes()
    if (
        receipt.get("name") != name
        or type(receipt.get("bytes")) is not int
        or receipt.get("bytes") != len(body)
        or receipt.get("sha256") != hashlib.sha256(body).hexdigest()
        or receipt.get("tls_verified") is not True
        or type(receipt.get("http_status")) is not int
        or receipt.get("http_status") != 200
    ):
        raise ImportRefused("original source capture does not match its positive receipt")
    try:
        captured = datetime.fromisoformat(str(receipt.get("retrieved_utc")))
    except ValueError:
        raise ImportRefused("source receipt has no valid acquisition date") from None
    if captured.tzinfo is None or captured > datetime.now(UTC):
        raise ImportRefused("source receipt date is naive or in the future")
    actual = receipt.get("url")
    if not isinstance(actual, str):
        raise ImportRefused("source receipt has no HTTPS acquisition URL")
    checked_url(actual)
    if receipt.get("origin_url", actual) != expected_url:
        raise ImportRefused("source receipt is not bound to the expected publisher resource")
    if actual != expected_url:
        mirror = receipt.get("mirror_base")
        if not isinstance(mirror, str) or not mirror:
            raise ImportRefused("source receipt requires an explicit mirror declaration")
        if checked_url(mirror).query or actual != mirror.rstrip("/") + "/" + name:
            raise ImportRefused("source receipt does not match its declared mirror resource")
    return receipt


def read_captures(directory: Path) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """Review exact rights and full count/ID captures before constructing observations.

    Parameters
    ----------
    directory : pathlib.Path
        Complete original sources with their acquisition receipts.

    Returns
    -------
    tuple
        All observations and verified capture manifest records.

    Raises
    ------
    ImportRefused
        Rights, original custody or either complete native source contract differs.
    """
    pages = sorted(
        path
        for path in directory.glob("ARPAE_PAGE_*.json")
        if not path.name.endswith(".receipt.json")
    )
    if (directory / "ARPAE_COMPLETE.json").exists():
        if pages:
            raise ImportRefused("capture contains ambiguous complete and paginated Italian sources")
        pages = [directory / "ARPAE_COMPLETE.json"]
    if not pages:
        raise ImportRefused("capture has no complete Italian feature pages")
    receipts = [
        verified_receipt(directory, name, expected_url=url) for name, url in BASE_URLS.items()
    ]
    total, size = page_plan(directory / "ARPAE_LAYER.json", directory / "ARPAE_COUNT.json")
    if pages[0].name != "ARPAE_COMPLETE.json" and [path.name for path in pages] != [
        f"ARPAE_PAGE_{index:04d}.json" for index, _ in enumerate(range(0, total, size))
    ]:
        raise ImportRefused("Italian capture page filenames do not equal the complete page plan")
    receipts.extend(
        verified_receipt(directory, page.name, expected_url=page_url(index * size, size))
        for index, page in enumerate(pages)
    )
    swiss = read_json(directory / "SFOE_METADATA.json")
    italian = read_json(directory / "ARPAE_METADATA.json")
    if swiss.get("success") is not True or italian.get("success") is not True:
        raise ImportRefused("source catalogue did not report a successful native result")
    swiss_meta = object_fields(swiss.get("result"))
    italian_meta = object_fields(italian.get("result"))
    resources = object_rows(swiss_meta.get("resources"))
    exact = [
        resource
        for resource in resources
        if resource.get("id") == "6a31d549-be3e-4727-a4f8-05d7d2ab5c54"
    ]
    if (
        len(exact) != 1
        or exact[0].get("url") != SFOE_URL
        or exact[0].get("rights") != TERMS_URL
        or exact[0].get("license") != TERMS_URL
    ):
        raise ImportRefused("Swiss exact resource does not bind the reviewed terms-by grant")
    if (
        hashlib.sha256((directory / "SFOE_TERMS.html").read_bytes()).hexdigest()
        not in APPROVED_TERMS_SHA256S
    ):
        raise ImportRefused("Swiss terms capture differs and needs a fresh source-specific review")
    italian_resources = object_rows(italian_meta.get("resources"))
    italian_exact = [
        resource
        for resource in italian_resources
        if resource.get("id") == "1af54eda-b778-4b21-a8dc-e4710600d25d"
    ]
    if (
        len(italian_exact) != 1
        or italian_exact[0].get("url") != ARPAE_SERVICE
        or italian_meta.get("license_id") != "CC BY 4.0 (Creative Commons - Attribuzione)"
    ):
        raise ImportRefused(
            "Italian exact REST resource does not bind the reviewed CC-BY-4.0 grant"
        )
    by_name = {receipt["name"]: receipt for receipt in receipts}
    swiss_date = (
        datetime.fromisoformat(str(by_name["SFOE_ORIGINAL.csv.zip"]["retrieved_utc"]))
        .astimezone(UTC)
        .date()
        .isoformat()
    )
    italian_date = (
        datetime.fromisoformat(str(by_name[pages[-1].name]["retrieved_utc"]))
        .astimezone(UTC)
        .date()
        .isoformat()
    )
    rows = read_swiss(
        directory / "SFOE_ORIGINAL.csv.zip",
        retrieved=swiss_date,
        source_date=str(exact[0].get("modified", ""))[:10],
    )
    rows.extend(
        read_italian(
            directory / "ARPAE_LAYER.json",
            directory / "ARPAE_COUNT.json",
            directory / "ARPAE_IDS.json",
            pages,
            retrieved=italian_date,
        )
    )
    rows.sort(key=lambda row: (row["source"], row["source_record_id"].casefold()))
    return rows, receipts


def main() -> None:
    """Review complete frozen captures without refreshing or rewriting them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    try:
        rows, receipts = read_captures(args.directory)
    except (OSError, ImportRefused):
        print("CAPTURE CHECK FAILED: custody, acquisition or source-specific rights require review")
        raise SystemExit(1) from None
    print(
        json.dumps(
            {
                "observations": len(rows),
                "verified_captures": len(receipts),
                "scientific_acceptance": "not established",
            }
        )
    )


if __name__ == "__main__":
    main()
