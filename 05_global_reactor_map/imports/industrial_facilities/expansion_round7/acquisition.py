# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — bounded source acquisition
"""Explicitly acquire complete publisher sources into new private external custody."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import math
import ssl
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"

from .capture import BASE_URLS, REPOSITORY, checked_url, page_plan, page_url, read_captures
from .contracts import MAX_BYTES, ImportRefused


def download(
    url: str,
    *,
    ca_file: Path | None = None,
    timeout: float = 40,
    max_bytes: int = MAX_BYTES,
    deadline_seconds: float = 90,
) -> bytes:
    """Read a bounded anonymous HTTPS response, refusing every redirect.

    Parameters
    ----------
    url : str
        Source URL or explicitly trusted institutional mirror.
    ca_file : pathlib.Path, optional
        Additional trusted CA for the explicit mirror, never an unverified TLS mode.
    timeout : float
        Finite positive socket timeout, distinct from the checked elapsed deadline.
    max_bytes : int
        Positive maximum response size.
    deadline_seconds : float
        Finite positive elapsed deadline checked between bounded response reads.

    Returns
    -------
    bytes
        Actual HTTP 200 response bytes.

    Raises
    ------
    ImportRefused
        URL, limits, response status, deadline or body size is invalid.
    """
    parsed = checked_url(url)
    if (
        not math.isfinite(timeout)
        or timeout <= 0
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
        or type(max_bytes) is not int
        or max_bytes <= 0
    ):
        raise ImportRefused("source limits must be finite and positive")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    connection = http.client.HTTPSConnection(
        str(parsed.hostname), port=parsed.port, timeout=timeout, context=context
    )
    deadline = time.monotonic() + deadline_seconds
    try:
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request(
            "GET",
            target,
            headers={
                "Accept-Encoding": "identity",
                "User-Agent": "Atlas-Reactorum-source-capture/7",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ImportRefused(
                f"source returned HTTP {response.status}, requires HTTP 200; redirects are refused"
            )
        pieces: list[bytes] = []
        length = 0
        while True:
            if time.monotonic() > deadline:
                raise ImportRefused("source exceeds its checked acquisition deadline")
            piece = response.read1(min(65536, max_bytes + 1 - length))
            if not piece:
                break
            length += len(piece)
            if length > max_bytes:
                raise ImportRefused("source exceeds its acquisition byte limit")
            pieces.append(piece)
        return b"".join(pieces)
    finally:
        connection.close()


def acquire(
    directory: Path, *, mirror_base: str = "", ca_file: Path | None = None
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """Capture a new private original set, retaining any partial acquisition on failure.

    Parameters
    ----------
    directory : pathlib.Path
        New external custody directory; existing targets and repository paths refused.
    mirror_base : str, optional
        Explicit trusted HTTPS mirror serving each fixed source filename.
    ca_file : pathlib.Path, optional
        Trusted mirror CA.

    Returns
    -------
    tuple
        Complete observations and positive receipts after source-contract checks.

    Raises
    ------
    ImportRefused
        Target, mirror, complete count or publisher page limit is invalid.
    """
    if (
        directory.resolve().is_relative_to(REPOSITORY)
        or directory.exists()
        or directory.is_symlink()
    ):
        raise ImportRefused("new capture directory must be external and previously absent")
    if mirror_base and checked_url(mirror_base).query:
        raise ImportRefused("explicit mirror base must not contain a query")
    directory.mkdir(parents=True)

    def capture(name: str, origin: str) -> None:
        """Persist actual source bytes and their receipt under a fixed resource name."""
        url = mirror_base.rstrip("/") + "/" + name if mirror_base else origin
        started = datetime.now(UTC).isoformat()
        body = download(url, ca_file=ca_file)
        with (directory / name).open("xb") as handle:
            handle.write(body)
        receipt = {
            "name": name,
            "url": url,
            "origin_url": origin,
            "mirror_base": mirror_base,
            "retrieved_utc": started,
            "tls_verified": True,
            "http_status": 200,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        with (directory / (name + ".receipt.json")).open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")

    for name, url in BASE_URLS.items():
        capture(name, url)
    count, size = page_plan(directory / "ARPAE_LAYER.json", directory / "ARPAE_COUNT.json")
    for page, offset in enumerate(range(0, count, size)):
        name = "ARPAE_COMPLETE.json" if count <= size else f"ARPAE_PAGE_{page:04d}.json"
        capture(name, page_url(offset, size))
    return read_captures(directory)


def main() -> None:
    """Acquire and check a new original set; partial failed captures remain inspectable."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--mirror-base", default="")
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args()
    try:
        rows, receipts = acquire(args.directory, mirror_base=args.mirror_base, ca_file=args.ca_file)
    except (OSError, http.client.HTTPException, ImportRefused):
        print("ACQUISITION FAILED: transport, custody or source-specific review requires attention")
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
