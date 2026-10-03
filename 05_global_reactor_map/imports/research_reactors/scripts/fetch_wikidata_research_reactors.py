#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/scripts/fetch_wikidata_research_reactors.py
"""Build a CC0 discovery snapshot of Wikidata research-reactor records.

The script deliberately does not query or scrape the IAEA RRDB.  Wikidata is
used as an openly reusable discovery index; downstream users must verify
individual records against a regulator, laboratory, or the RRDB.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import os
import re
import ssl
import tempfile
import time
import urllib.parse
import urllib.request
from collections.abc import Iterator
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
ENTITY_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "reactor-research-library/1.0 (open research-reactor discovery dataset)"
FIELDS = [
    "stable_id",
    "name",
    "aliases",
    "country",
    "lat",
    "lon",
    "precision",
    "reactor_type",
    "status",
    "purpose",
    "thermal_power_mw",
    "operator",
    "first_criticality",
    "shutdown_date",
    "source_url",
    "source_role",
    "retrieved",
    "license",
    "verification_notes",
]
EXCLUDED_NON_FACILITY_ITEMS = {
    # Reactor family/design item rather than one physical reactor.  Wikidata
    # currently models it as an instance of research reactor.
    "Q2646841": "SLOWPOKE reactor family",
}


def statements(entity: dict[str, Any], prop: str) -> list[dict[str, Any]]:
    """Extract an entity's claim statements."""
    claims = entity.get("claims", {}).get(prop, [])
    usable = [c for c in claims if c.get("rank") != "deprecated"]
    preferred = [c for c in usable if c.get("rank") == "preferred"]
    return preferred or usable


def values(entity: dict[str, Any], prop: str) -> list[dict[str, Any]]:
    """Collect value objects from already validated source claims."""
    out: list[dict[str, Any]] = []
    for claim in statements(entity, prop):
        snak = claim.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        out.append(snak["datavalue"]["value"])
    return out


def entity_ids(entity: dict[str, Any], prop: str) -> list[str]:
    """Collect the entity identifiers from the query results."""
    result: list[str] = []
    for value in values(entity, prop):
        result.append(value["id"])
    return result


def label(entity: dict[str, Any], qid: str = "") -> str:
    """Read an entity's label in the preferred language."""
    labels = entity.get("labels", {})
    for lang in ("en", "mul", "de", "fr", "es", "ru"):
        if lang in labels:
            text: str = labels[lang]["value"].strip()
            return text
    # Core reactor entities are fetched with labels in all languages so a
    # human-readable local name is preferable to exposing a bare Q identifier.
    if labels:
        fallback: str = next(iter(labels.values()))["value"].strip()
        return fallback
    return qid


def labels(qids: list[str], entities: dict[str, dict[str, Any]]) -> str:
    """Join distinct referenced source labels without inventing missing names."""
    names = {label(entities[qid], qid) for qid in qids}
    return "|".join(sorted((x for x in names if x), key=str.casefold))


def time_value(entity: dict[str, Any], prop: str) -> str:
    """Retain a source retirement date at its stated calendar precision."""
    vals = values(entity, prop)
    if not vals:
        return ""
    raw = vals[0].get("time", "")
    precision = vals[0].get("precision", 0)
    match = re.match(r"^[+-](\d{4,})-(\d{2})-(\d{2})T", raw)
    if not match:
        return ""
    year, month, day = match.groups()
    if precision >= 11:
        return f"{year}-{month}-{day}"
    if precision == 10:
        return f"{year}-{month}"
    return year if precision == 9 else ""


def coordinates(entity: dict[str, Any]) -> tuple[str, str]:
    """Retain source latitude/longitude at the historical display precision."""
    vals = values(entity, "P625")
    if not vals:
        return "", ""
    value = vals[0]
    lat, lon = value.get("latitude"), value.get("longitude")
    return f"{lat:.7f}".rstrip("0").rstrip("."), f"{lon:.7f}".rstrip("0").rstrip(".")


def normalized_status(
    entity: dict[str, Any], entities: dict[str, dict[str, Any]]
) -> tuple[str, str]:
    """Classify explicit status labels; conflicting labels remain unknown."""
    raw = labels(entity_ids(entity, "P5817"), entities)
    mapping = {
        "operational": "operational",
        "operating": "operational",
        "active": "operational",
        "in use": "operational",
        "under construction": "under_construction",
        "construction": "under_construction",
        "decommissioned": "decommissioned",
        "dismantled": "decommissioned",
        "demolished": "decommissioned",
        "shutdown": "shutdown",
        "shut down": "shutdown",
        "closed": "shutdown",
        "retired": "shutdown",
        "inactive": "shutdown",
        "not in use": "shutdown",
        "not operational": "shutdown",
        "permanently closed": "shutdown",
        "decommissioning": "decommissioning",
        "nuclear decommissioning": "decommissioning",
        "planned": "planned",
        "proposed": "planned",
        "proposed building or structure": "planned",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "abandoned": "cancelled",
    }
    observed = {mapping.get(part.casefold(), "unknown") for part in raw.split("|") if part}
    if len(observed) == 1 and "unknown" not in observed:
        return observed.pop(), raw
    if not observed or observed == {"unknown"}:
        if time_value(entity, "P576") or time_value(entity, "P730"):
            return "shutdown", raw
    return "unknown", raw


QUERY = "SELECT DISTINCT ?item ?class WHERE {\n      ?item wdt:P31 ?class.\n      ?class wdt:P279* wd:Q1438105.\n    } ORDER BY ?item ?class"
ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parents[2]
PROPERTIES = ("P17", "P137", "P366", "P5817", "P576", "P730", "P625")


def render_rows(
    classes_by_item: dict[str, set[str]], entities: dict[str, dict[str, Any]], *, retrieved: str
) -> bytes:
    """Render source-backed discovery rows without inferring power or criticality."""
    rows = []
    for qid in sorted(classes_by_item, key=lambda q: int(q[1:])):
        entity = entities[qid]
        name = label(entity, qid)
        alias_values: set[str] = set()
        for lang in ("en", "mul"):
            alias_values.update(a["value"].strip() for a in entity.get("aliases", {}).get(lang, []))
        alias_values.discard(name)
        lat, lon = coordinates(entity)
        status, raw_status = normalized_status(entity, entities)
        shutdown = time_value(entity, "P730") or time_value(entity, "P576")
        type_names = labels(sorted(classes_by_item[qid]), entities) or "research reactor"
        notes = [
            "CC0 Wikidata discovery record; community-edited and not authoritative.",
            "Coordinates, type, dates, and status require verification against a regulator, operator, or IAEA RRDB.",
            "First criticality and thermal power are blank unless an unambiguous reusable source supplies those exact concepts.",
        ]
        if raw_status:
            notes.append(f"Wikidata raw status label: {raw_status}.")
        elif status == "shutdown" and shutdown:
            notes.append(
                "Status normalized to shutdown only because Wikidata supplies a retirement or dissolution date."
            )
        if not lat:
            notes.append("No coordinate assertion was available in the retrieved Wikidata entity.")
        rows.append(
            {
                "stable_id": "wikidata-" + qid.lower(),
                "name": name,
                "aliases": "|".join(sorted(alias_values, key=str.casefold)),
                "country": labels(entity_ids(entity, "P17"), entities),
                "lat": lat,
                "lon": lon,
                "precision": "unknown",
                "reactor_type": type_names,
                "status": status,
                "purpose": labels(entity_ids(entity, "P366"), entities),
                "thermal_power_mw": "",
                "operator": labels(entity_ids(entity, "P137"), entities),
                "first_criticality": "",
                "shutdown_date": shutdown,
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
                "source_role": "open discovery registry",
                "retrieved": retrieved,
                "license": "CC0 1.0",
                "verification_notes": " ".join(notes),
            }
        )

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def check_https(url: str) -> None:
    """Require anonymous HTTPS for retrieval and every actual redirect."""
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.port == 0
        or parsed.fragment
        or any(c.isspace() for c in url)
    ):
        raise ValueError("source URL must be valid anonymous HTTPS")


class SourceRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse insecure or credential-bearing server redirect destinations."""

    max_redirections = 5

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Check a real destination before urllib follows it."""
        check_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get_json(
    url: str,
    attempts: int = 4,
    *,
    ca_file: Path | None = None,
    timeout: float = 30,
    max_bytes: int = 16 * 1024 * 1024,
    backoff: float = 0.1,
) -> dict[str, Any]:
    """Retrieve one JSON object over verified HTTPS.

    Parameters
    ----------
    url : str
        Anonymous HTTPS endpoint; every redirect must retain that boundary.
    attempts : int
        Maximum network attempts, from one to four. Invalid JSON is not retried.
    ca_file : Path or None
        Additional trust roots for an explicit mirror.
    timeout : float
        Positive finite timeout in seconds per socket operation.
    max_bytes : int
        Positive response-body limit in bytes; defaults to 16 MiB.
    backoff : float
        Initial retry delay in seconds, from zero to one, doubled per retry.

    Returns
    -------
    dict
        Complete decoded object without a Wikidata API error.

    Raises
    ------
    ValueError
        The endpoint, bounds, status, body or decoded shape is refused.
    RuntimeError
        All permitted network attempts failed.
    """
    check_https(url)
    if (
        type(attempts) is not int
        or not 1 <= attempts <= 4
        or not math.isfinite(timeout)
        or timeout <= 0
        or type(max_bytes) is not int
        or max_bytes <= 0
        or not math.isfinite(backoff)
        or not 0 <= backoff <= 1
    ):
        raise ValueError("request limits must be finite, positive and bounded")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context), SourceRedirect()
    )
    error: OSError | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            with opener.open(request, timeout=timeout) as response:
                if response.status != 200:
                    raise ValueError(f"Wikidata returned HTTP {response.status}")
                body = response.read(max_bytes + 1)
        except OSError as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(backoff * 2**attempt)
            continue
        if len(body) > max_bytes:
            raise ValueError("source response exceeds its byte limit")
        loaded = json.loads(body)
        if not isinstance(loaded, dict) or "error" in loaded:
            raise ValueError("Wikidata response must be an object without an API error")
        return loaded
    raise RuntimeError(f"request failed after {attempts} attempts") from error


def discover(payload: object) -> dict[str, set[str]]:
    """Read every original DISTINCT class binding and exclude the named family."""
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("results"), dict)
        or not isinstance(payload["results"].get("bindings"), list)
    ):
        raise ValueError("discovery response requires its binding list")
    classes: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    for binding in payload["results"]["bindings"]:
        if not isinstance(binding, dict):
            raise ValueError("discovery binding must be an object")
        identities = []
        for field in ("item", "class"):
            value = binding.get(field)
            if (
                not isinstance(value, dict)
                or value.get("type") != "uri"
                or not isinstance(value.get("value"), str)
            ):
                raise ValueError("discovery identity must be its source URI")
            match = re.fullmatch(
                r"https?://www\.wikidata\.org/entity/(Q[1-9][0-9]*)", value["value"]
            )
            if not match:
                raise ValueError("discovery requires canonical Wikidata item identities")
            identities.append(match[1])
        item, klass = identities
        if (item, klass) in seen:
            raise ValueError("discovery contains a duplicate DISTINCT binding")
        seen.add((item, klass))
        classes.setdefault(item, set()).add(klass)
    for qid in EXCLUDED_NON_FACILITY_ITEMS:
        classes.pop(qid, None)
    if not classes:
        raise ValueError("discovery contains no facility items")
    return classes


def chunks(values: list[str], size: int = 50) -> Iterator[list[str]]:
    """Yield bounded entity batches in their already defined order."""
    if not 1 <= size <= 50:
        raise ValueError("entity batch size must be between 1 and 50")
    for start in range(0, len(values), size):
        yield values[start : start + size]


def validate_entities(
    entities: object, expected: set[str], *, core: bool
) -> dict[str, dict[str, Any]]:
    """Require complete exact entity identities and well-formed source metadata."""
    if not isinstance(entities, dict) or set(entities) != expected:
        raise ValueError("entity response must contain every exact requested identity")
    for qid, entity in entities.items():
        if (
            not isinstance(entity, dict)
            or entity.get("id") != qid
            or "missing" in entity
            or "redirects" in entity
            or not re.fullmatch(r"Q[1-9][0-9]*", qid)
        ):
            raise ValueError("source entity must retain its exact nonmissing item identity")
        labels = entity.get("labels", {})
        if not isinstance(labels, dict) or any(
            not isinstance(v, dict) or not isinstance(v.get("value"), str) or not v["value"].strip()
            for v in labels.values()
        ):
            raise ValueError("entity labels must contain nonempty source text")
        if core:
            aliases = entity.get("aliases", {})
            claims = entity.get("claims", {})
            if (
                not isinstance(aliases, dict)
                or any(
                    not isinstance(v, list)
                    or any(
                        not isinstance(a, dict) or not isinstance(a.get("value"), str) for a in v
                    )
                    for v in aliases.values()
                )
                or not isinstance(claims, dict)
            ):
                raise ValueError("core entity requires its alias and claim objects")
            for prop in PROPERTIES:
                statements = claims.get(prop, [])
                if not isinstance(statements, list) or any(
                    not isinstance(c, dict)
                    or c.get("rank") not in {"normal", "preferred", "deprecated"}
                    or not isinstance(c.get("mainsnak"), dict)
                    or c["mainsnak"].get("snaktype") not in {"value", "novalue", "somevalue"}
                    or not isinstance(c["mainsnak"].get("datavalue", {}), dict)
                    for c in statements
                ):
                    raise ValueError("consumed claims require their rank and source snak objects")
                for claim in statements:
                    snak = claim["mainsnak"]
                    if snak["snaktype"] != "value":
                        continue
                    value = snak.get("datavalue", {}).get("value")
                    if not isinstance(value, dict):
                        raise ValueError("consumed value claims require their source value objects")
                    if prop in {"P17", "P137", "P366", "P5817"}:
                        if (
                            value.get("entity-type") != "item"
                            or not isinstance(value.get("id"), str)
                            or not re.fullmatch(r"Q[1-9][0-9]*", value["id"])
                        ):
                            raise ValueError("referenced claims require exact source Q identifiers")
                    elif prop == "P625":
                        lat, lon = value.get("latitude"), value.get("longitude")
                        if (
                            not isinstance(lat, (int, float))
                            or not isinstance(lon, (int, float))
                            or isinstance(lat, bool)
                            or isinstance(lon, bool)
                            or not math.isfinite(lat)
                            or not math.isfinite(lon)
                            or not -90 <= lat <= 90
                            or not -180 <= lon <= 180
                            or value.get("globe") != "http://www.wikidata.org/entity/Q2"
                        ):
                            raise ValueError("coordinates require finite Earth latitude/longitude")
                    elif (
                        not isinstance(value.get("time"), str)
                        or type(value.get("precision")) is not int
                        or not 0 <= value["precision"] <= 14
                    ):
                        raise ValueError("dates require their source time string and precision")
    return entities


def referenced_ids(classes: dict[str, set[str]], core: dict[str, dict[str, Any]]) -> set[str]:
    """Collect only the original country/operator/purpose/status/class references."""
    result = {qid for values in classes.values() for qid in values}
    for entity in core.values():
        for prop in ("P17", "P137", "P366", "P5817"):
            result.update(entity_ids(entity, prop))
    return result - set(core)


def validate_cache(loaded: object) -> tuple[dict[str, set[str]], dict[str, dict[str, Any]]]:
    """Validate discovery and every exact core/reference identity.

    Parameters
    ----------
    loaded : object
        Version 1.0.0 cache with its exact ISO capture date and source replies.

    Returns
    -------
    tuple
        Facility-to-class identities and merged validated entity records.

    Raises
    ------
    ValueError
        Discovery, identities or any consumed source value is incomplete or
        malformed. Unknown snaks are valid absence, not fabricated values.
    """
    if not isinstance(loaded, dict) or loaded.get("schema_version") != "1.0.0":
        raise ValueError("cache requires its versioned source envelope")
    captured = loaded.get("captured_at")
    if not isinstance(captured, str) or dt.date.fromisoformat(captured).isoformat() != captured:
        raise ValueError("cache requires its exact ISO capture date")
    classes = discover(loaded.get("discovery"))
    core = validate_entities(loaded.get("core"), set(classes), core=True)
    references = referenced_ids(classes, core)
    labels = validate_entities(loaded.get("labels"), references, core=False)
    return classes, {**core, **labels}


def fetch_entities(
    qids: set[str],
    props: str = "labels|aliases|claims",
    languages: str | None = None,
    *,
    endpoint: str = ENTITY_API,
    ca_file: Path | None = None,
    attempts: int = 4,
    timeout: float = 30,
) -> dict[str, dict[str, Any]]:
    """Acquire every sorted fifty-item batch and refuse partial entity replies."""
    if any(not re.fullmatch(r"Q[1-9][0-9]*", qid) for qid in qids):
        raise ValueError("entity acquisition requires valid Q identifiers")
    result: dict[str, dict[str, Any]] = {}
    for batch in chunks(sorted(qids, key=lambda q: int(q[1:]))):
        params = {
            "action": "wbgetentities",
            "format": "json",
            "formatversion": "2",
            "ids": "|".join(batch),
            "props": props,
        }
        if languages:
            params.update(languages=languages, languagefallback="1")
        full = endpoint + "?" + urllib.parse.urlencode(params)
        payload = get_json(full, ca_file=ca_file, attempts=attempts, timeout=timeout)
        result.update(
            validate_entities(payload.get("entities"), set(batch), core=languages is None)
        )
    return result


def capture(
    *,
    query_endpoint: str = SPARQL_ENDPOINT,
    entity_endpoint: str = ENTITY_API,
    ca_file: Path | None = None,
    attempts: int = 4,
    timeout: float = 30,
) -> dict[str, Any]:
    """Capture the exact query, complete core entities and all referenced labels."""
    payload = get_json(
        query_endpoint + "?" + urllib.parse.urlencode({"query": QUERY, "format": "json"}),
        ca_file=ca_file,
        attempts=attempts,
        timeout=timeout,
    )
    classes = discover(payload)
    core = fetch_entities(
        set(classes), endpoint=entity_endpoint, ca_file=ca_file, attempts=attempts, timeout=timeout
    )
    references = referenced_ids(classes, core)
    labels = fetch_entities(
        references,
        props="labels",
        languages="en|mul|de|fr|es|ru",
        endpoint=entity_endpoint,
        ca_file=ca_file,
        attempts=attempts,
        timeout=timeout,
    )
    return {
        "schema_version": "1.0.0",
        "captured_at": dt.date.today().isoformat(),
        "discovery": payload,
        "core": core,
        "labels": labels,
    }


def check_output(path: Path, inputs: tuple[Path, ...] = ()) -> None:
    """Protect accepted Atlas files and resolved input/cache/CA destinations."""
    target = path.resolve()
    if target.is_relative_to(LIBRARY) or target in {p.resolve() for p in inputs}:
        raise ValueError("output must be separate from accepted Atlas files and inputs")


def atomic_write(path: Path, body: bytes) -> None:
    """Atomically replace one candidate and remove failed write/close temporaries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(body)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def render(loaded: object, *, retrieved: str) -> bytes:
    """Validate the full cache and exact row date before UTF-8 preparation."""
    if dt.date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO date")
    classes, entities = validate_cache(loaded)
    return render_rows(classes, entities, retrieved=retrieved)


def build(loaded: object, output: Path, *, retrieved: str, inputs: tuple[Path, ...] = ()) -> None:
    """Validate, render and atomically replace one isolated TSV candidate.

    Parameters
    ----------
    loaded : object
        Complete captured source envelope; accepted data are never refreshed
        implicitly.
    output : Path
        Destination outside Atlas and separate from every resolved input.
    retrieved : str
        Exact ISO row date; does not change the source cache capture date.
    inputs : tuple of Path
        Source/cache/CA files protected from destination aliasing.

    Raises
    ------
    ValueError
        Source, date or output destination violates the candidate contract.
    OSError
        Writing or atomic replacement failed; the owned temporary is removed.
    UnicodeError
        Complete rendering cannot be encoded as UTF-8 before any write.
    """
    check_output(output, inputs)
    atomic_write(output, render(loaded, retrieved=retrieved))


def main(argv: list[str] | None = None) -> int:
    """Prepare a read-only offline candidate or an explicit live/cache refresh."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--cache-out", type=Path)
    parser.add_argument("--query-url", default=SPARQL_ENDPOINT)
    parser.add_argument("--entity-url", default=ENTITY_API)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        inputs = tuple(p for p in (args.cache, args.ca_file) if p is not None)
        check_output(args.out, (*inputs, *((args.cache_out,) if args.cache_out else ())))
        if args.refresh:
            if args.cache or args.cache_out is None:
                raise ValueError("refresh requires a separate cache output and no offline cache")
            check_output(args.cache_out, (*inputs, args.out))
            loaded = capture(
                query_endpoint=args.query_url, entity_endpoint=args.entity_url, ca_file=args.ca_file
            )
            body = render(loaded, retrieved=args.date or loaded["captured_at"])
            cache = (json.dumps(loaded, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            atomic_write(args.cache_out, cache)
            atomic_write(args.out, body)
        else:
            if (
                args.cache is None
                or args.cache_out
                or args.ca_file
                or args.query_url != SPARQL_ENDPOINT
                or args.entity_url != ENTITY_API
            ):
                raise ValueError("offline build requires a cache; network options require refresh")
            loaded = json.loads(args.cache.read_bytes())
            validate_cache(loaded)
            build(loaded, args.out, retrieved=args.date or loaded["captured_at"], inputs=inputs)
    except (OSError, UnicodeError, ValueError, TypeError, RuntimeError, csv.Error) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote isolated research-reactor candidate to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
