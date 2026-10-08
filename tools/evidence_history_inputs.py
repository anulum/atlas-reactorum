# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native history input shapes before semantic admission.

"""Check complete history wire shapes against the owning profile schema.

Schema success does not verify journal hashes, chronology, claim/source binding
or curator decisions. The existing native history model owns those checks.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Literal, NoReturn, cast

try:
    from jsonschema import Draft202012Validator, FormatChecker, SchemaError, ValidationError
except ImportError:
    print("Evidence history input shape refused.", file=sys.stderr)
    raise SystemExit(1) from None

PacketKind = Literal["profiles", "history", "proposal"]
PROFILE_SCHEMA = (
    Path(__file__).resolve().parents[1] / "metadata/evidence_profiles/profiles.schema.json"
)


def _mapping(value: object) -> dict[str, object]:
    """Read one original schema object while retaining unknown member values."""
    if not isinstance(value, dict):
        raise ValueError("Owning profile schema is unavailable")
    return cast(dict[str, object], value)


def _record(properties: dict[str, object]) -> dict[str, object]:
    """Describe exactly the required wire members without accepting extra cells."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def validate_packet(kind: PacketKind, value: object) -> None:
    """Validate complete wire shapes before the native model interprets them.

    Parameters
    ----------
    kind : {'profiles', 'history', 'proposal'}
        Existing profile, journal or original pending-proposal contract.
    value : object
        Parsed original JSON. Source cells are never normalised or rewritten.

    Raises
    ------
    OSError
        The owning profile schema cannot be read.
    ValueError
        The owning schema is malformed or its component is unavailable.
    SchemaError
        A supplied owning schema violates JSON Schema Draft 2020-12.
    ValidationError
        A wire cell does not have its original declared shape.

    Notes
    -----
    This verifies shapes only. Journal integrity, chronology, source binding,
    anonymous HTTPS and curator eligibility remain with their native owners.
    """
    profile = _mapping(json.loads(PROFILE_SCHEMA.read_text(encoding="utf8")))
    Draft202012Validator.check_schema(profile)
    properties = _mapping(profile["properties"])
    source = _mapping(_mapping(properties["sources"])["items"])
    record = _mapping(_mapping(properties["records"])["items"])
    claim = _mapping(_mapping(_mapping(record["properties"])["claims"])["items"])
    digest: dict[str, object] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    text: dict[str, object] = {"type": "string"}
    date: dict[str, object] = {"type": "string", "format": "date-time"}
    dates = _record(
        {
            "atlas_observed_at": date,
            "source_acquired_at": {"type": ["string", "null"], "format": "date-time"},
            "claim_reviewed_on": {"type": ["string", "null"], "format": "date"},
            "source_event_on": {"type": "null"},
            "source_published_on": {"type": "null"},
        }
    )
    revision = _record(
        {
            "revision_sha256": digest,
            "profile_sha256": digest,
            "state": {"const": "present"},
            "claim": claim,
            "source": source,
            "changes": {"type": "array", "items": text},
            "dates": dates,
        }
    )
    proposal_input = _record(
        {
            "proposed_statement": text,
            "source_url": text,
            "locator": text,
            "reason": text,
            "submitted_by": text,
            "proposed_at": date,
        }
    )
    journal = _record(
        {
            "schema_version": {"const": "atlas-evidence-history-1.0.0"},
            "metadata_license": {"const": "AGPL-3.0-or-later"},
            "source_rights": {"const": "catalogue-only; original not redistributed"},
            "snapshots": {
                "type": "array",
                "minItems": 1,
                "items": _record({"profile_sha256": digest, "document": profile}),
            },
            "imports": {
                "type": "array",
                "minItems": 1,
                "items": _record({"profile_sha256": digest, "observed_at": date}),
            },
        }
    )
    pending = _record(
        {
            "schema_version": {"const": "atlas-correction-proposal-1.0.0"},
            "state": {"const": "pending"},
            "metadata_license": {"const": "AGPL-3.0-or-later"},
            "source_rights": {"const": "catalogue-only; original not redistributed"},
            "history_sha256": digest,
            "entry_id": text,
            "claim_id": text,
            "original_revision": revision,
            "proposal": proposal_input,
            "review": {"type": "null"},
            "publication_effect": {"const": "none; accepted source data remain unchanged"},
            "proposal_sha256": digest,
        }
    )
    schemas = {"profiles": profile, "history": journal, "proposal": pending}
    Draft202012Validator(schemas[kind], format_checker=FormatChecker()).validate(value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse duplicate JSON member names instead of selecting the last value."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def _constant(value: str) -> NoReturn:
    """Refuse every non-JSON numeric constant before schema admission."""
    raise ValueError("Non-JSON numeric constant")


def _float(value: str) -> float:
    """Refuse an overflowing JSON number without replacing it with null."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite JSON number")
    return number


def main(argv: list[str] | None = None) -> int:
    """Validate original UTF-8 JSON on stdin without echoing caller input.

    Parameters
    ----------
    argv : list of str or None
        Explicit packet kind; None uses the actual process arguments.

    Returns
    -------
    int
        Zero for valid shapes, one for a fixed safe refusal.
    """
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in {"profiles", "history", "proposal"}:
        print("Evidence history input shape refused.", file=sys.stderr)
        return 1
    try:
        value: object = json.loads(
            sys.stdin.buffer.read().decode("utf8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
            parse_float=_float,
        )
        validate_packet(cast(PacketKind, args[0]), value)
    except (OSError, ValueError, KeyError, SchemaError, ValidationError):
        print("Evidence history input shape refused.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
