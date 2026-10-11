# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — frozen original and current reviewed profile admission.

"""Validate the complete reviewed product against its actual original and author inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker, SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import Schema

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from metadata.evidence_profiles.review_contract import (
    ReviewError,
    project_author_taxonomy,
    read_review_json,
)
from metadata.evidence_profiles.validate import ProfileError, validate_profiles


def validate_reviewed_profiles(
    root: Path,
    snapshot_sha256: str,
    reviews_path: Path,
    document: dict[str, object] | None = None,
) -> dict[str, object]:
    """Admit every current row while retaining the entire exact original profile.

    Parameters
    ----------
    root : pathlib.Path
        Complete source root with the original taxonomy, citations, audit and profile.
    snapshot_sha256 : str
        Explicit trusted original taxonomy hash.
    reviews_path : pathlib.Path
        Actual complete author input whose bytes are bound by the product.
    document : dict of str to object or None
        Whole reviewed product; None reads the maintained JSON product path.

    Returns
    -------
    dict of str to object
        Exact admitted product with complete original and current relationships.

    Raises
    ------
    ReviewError
        Input, shape, version, rights, hashes, originals, current rows or custody differ.
    """
    original_path = root / "metadata/evidence_profiles/profiles.json"
    try:
        original_bytes = original_path.read_bytes()
        review_bytes = reviews_path.read_bytes()
        original = validate_profiles(root, snapshot_sha256)
    except (OSError, ProfileError) as error:
        raise ReviewError("Reviewed profile source inputs cannot be validated.") from error
    if document is None:
        document = read_review_json(
            root / "04_interactive_presentation/data/taxonomy-reviewed-profiles.json"
        )
    directory = Path(__file__).parent
    try:
        schema = read_review_json(directory / "reviewed_profiles.schema.json")
        Draft202012Validator.check_schema(schema)
        registry: Registry[Schema] = Registry().with_resources(
            (
                f"urn:atlas-reactorum:{name}:{version}",
                Resource.from_contents(read_review_json(directory / filename)),
            )
            for name, filename, version in [
                ("evidence-profiles", "profiles.schema.json", "1.0.0"),
                ("author-review", "author_review.schema.json", "1.1.0"),
            ]
        )
        invalid = next(
            Draft202012Validator(
                schema, registry=registry, format_checker=FormatChecker()
            ).iter_errors(document),
            None,
        )
    except (ReviewError, SchemaError, Unresolvable) as error:
        raise ReviewError("Reviewed profile schema cannot be validated.") from error
    if invalid is not None:
        raise ReviewError("Reviewed profile schema validation failed.")
    if (
        type(document["record_count"]) is not int
        or document["record_count"] != original["record_count"]
    ):
        raise ReviewError("Reviewed profile count differs from its original catalogue.")
    inputs = cast(dict[str, object], original["inputs"])
    expected = {
        **inputs,
        "original_profiles_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "author_reviews_sha256": hashlib.sha256(review_bytes).hexdigest(),
    }
    author = read_review_json(reviews_path)
    if document["inputs"] != expected:
        raise ReviewError("Reviewed profile source hashes differ.")
    if document["original_profiles"] != original or document["author_reviews"] != author:
        raise ReviewError("Reviewed profile changed its original or author context.")
    current = project_author_taxonomy(root, snapshot_sha256, author)
    if document["records"] != current:
        raise ReviewError("Reviewed profile current rows differ from explicit revisions.")
    try:
        if (
            original_path.read_bytes() != original_bytes
            or reviews_path.read_bytes() != review_bytes
        ):
            raise ReviewError("Reviewed profile source changed during admission.")
        if validate_profiles(root, snapshot_sha256) != original:
            raise ReviewError("Reviewed profile original changed during admission.")
    except (OSError, ProfileError) as error:
        raise ReviewError("Reviewed profile source changed during admission.") from error
    return document


def main(argv: list[str] | None = None) -> int:
    """Validate the exact reviewed product through the same public API.

    Parameters
    ----------
    argv : list of str or None
        Explicit CLI arguments; None uses the actual process vector.

    Returns
    -------
    int
        Zero with the complete admitted product or one with fixed refusal text.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args(argv)
    try:
        document = read_review_json(args.input) if args.input is not None else None
        admitted = validate_reviewed_profiles(args.root, args.snapshot, args.reviews, document)
    except ReviewError as error:
        print("reviewed profiles: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(admitted, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
