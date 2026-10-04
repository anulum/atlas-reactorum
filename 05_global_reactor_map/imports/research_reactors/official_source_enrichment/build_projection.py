# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — reproducible primary field projection CLI
"""Build a complete source-bound research projection from an explicit reviewed ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from projection import project_fields, read_assertions


def read_baseline(path: Path) -> dict[str, dict[str, str]]:
    """Read the complete original cohort without coercing cells or losing identities.

    Parameters
    ----------
    path : pathlib.Path
        JSON baseline with its original ``rows`` array of string-valued cells.

    Returns
    -------
    dict of str to dict of str to str
        Original rows keyed by their exact unique stable identities.

    Raises
    ------
    ValueError
        The input is aliased, malformed, incomplete or contains duplicate identities.
    OSError
        The source cannot be read.
    """
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("research baseline symlinks are refused")
    document: object = json.loads(path.read_bytes())
    if not isinstance(document, dict) or not isinstance(document.get("rows"), list):
        raise ValueError("complete original research rows required")
    result: dict[str, dict[str, str]] = {}
    for original in document["rows"]:
        if not isinstance(original, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in original.items()
        ):
            raise ValueError("original research cells must remain strings")
        row: dict[str, str] = dict(original)
        identity = row.get("stable_id", "")
        if not identity.strip() or identity in result:
            raise ValueError("unique original research identity required")
        result[identity] = row
    return result


def build_projection(baseline: Path, ledger: Path, output: Path) -> dict[str, str | int]:
    """Write a fresh deterministic projection only after complete source review checks.

    Parameters
    ----------
    baseline, ledger : pathlib.Path
        Original cohort and exact reviewed field ledger. Their bytes are retained.
    output : pathlib.Path
        New JSON destination; existing files and aliases are never overwritten.

    Returns
    -------
    dict of str to str or int
        Product SHA-256, cohort size and actual selected-field count.

    Raises
    ------
    ValueError
        Source, field coverage or output custody is invalid.
    OSError
        Source reading or creation of the new destination fails.
    """
    original = read_baseline(baseline)
    assertions = read_assertions(ledger)
    projection = project_fields(original, assertions)
    if any(part.is_symlink() for part in (output, *output.parents)):
        raise ValueError("research projection output aliases are refused")
    selected = sum(row["selection"] == "selected" for row in projection.assertions)
    document = {
        "schema_version": "1.0.0",
        "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "record_count": len(projection.rows),
        "selected_fields": selected,
        "rows": list(projection.rows.values()),
        "assertions": projection.assertions,
    }
    body = (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(body)
    return {
        "sha256": hashlib.sha256(body).hexdigest(),
        "record_count": len(projection.rows),
        "selected_fields": selected,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Build from explicit source paths, with caller-safe failure text.

    Parameters
    ----------
    argv : sequence of str, optional
        CLI arguments; the current process arguments are used when absent.

    Returns
    -------
    int
        Zero after fresh output creation, two after a refused source or destination.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--assertions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        result = build_projection(options.baseline, options.assertions, options.output)
    except (OSError, ValueError):
        print(
            "Research projection refused; check source bindings and complete field review.",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
