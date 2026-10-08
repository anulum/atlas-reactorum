# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-field complete input conformance

"""Exercise original input contracts through the full source projection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metadata.facility_fields.inputs import MAX_SOURCE_BYTES, mapping, original_rows
from metadata.facility_fields.project import project

from ._facility_field_sources import PINS, document, replace_input, specification
from ._facility_field_sources import original_source as original_source


@pytest.mark.parametrize(
    "key",
    [
        "wri",
        "agstar-Mixed",
        "agstar-Cattle",
        "agstar-Poultry",
        "agstar-Swine",
        "agstar-Dairy",
        "br-epe-biomethane",
        "us-epa-lmop",
        "industrial7",
        "industrial6-snapshot",
    ],
)
def test_reviewed_source_byte_drift_refuses_projection(original_source: Path, key: str) -> None:
    """Reject byte drift in every parameterized reviewed publisher source."""
    path = original_source / str(specification(original_source, key)["path"])
    with path.open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="digest"):
        project(original_source)


@pytest.mark.parametrize("key", ["wri", "agstar", "industrial6", "industrial7"])
def test_reviewed_target_byte_drift_refuses_projection(original_source: Path, key: str) -> None:
    """Reject byte drift in each reviewed target dataset before projecting observations."""
    path = original_source / str(specification(original_source, key, target=True)["path"])
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="digest"):
        project(original_source)


@pytest.mark.parametrize(
    "failure",
    [
        "schema",
        "bool_schema",
        "source_scope",
        "target_scope",
        "pins_array",
        "sources_array",
        "target_array",
        "source_array",
        "format",
        "bool_count",
        "zero_count",
        "wrong_count",
        "string_count",
        "blank_path",
        "absolute_path",
        "parent_path",
        "empty_parts",
    ],
)
def test_complete_ledger_contract_is_enforced(original_source: Path, failure: str) -> None:
    """Reject invalid ledger schemas, scopes, formats, row counts and escaping source paths."""
    pins = document(original_source / PINS)
    source = mapping(mapping(pins["sources"])["wri"])
    if failure == "schema":
        pins["schema_version"] = 2
    elif failure == "bool_schema":
        pins["schema_version"] = True
    elif failure == "source_scope":
        mapping(pins["sources"]).pop("agstar-Dairy")
    elif failure == "target_scope":
        mapping(pins["target_datasets"]).pop("agstar")
    elif failure in {"sources_array", "target_array"}:
        pins["sources" if failure == "sources_array" else "target_datasets"] = []
    elif failure == "source_array":
        mapping(pins["sources"])["wri"] = []
    elif failure == "format":
        source["format"] = "unreviewed"
    elif failure in {"bool_count", "zero_count", "wrong_count", "string_count"}:
        source["rows"] = {
            "bool_count": True,
            "zero_count": 0,
            "wrong_count": 195,
            "string_count": "196",
        }[failure]
    else:
        source["path"] = {
            "blank_path": " ",
            "absolute_path": "/etc/passwd",
            "parent_path": "../escaped.csv",
            "empty_parts": ".",
        }.get(failure, source["path"])
    (original_source / PINS).write_text(json.dumps([] if failure == "pins_array" else pins))
    with pytest.raises(ValueError):
        project(original_source)


@pytest.mark.parametrize(
    "failure",
    [
        "root_alias",
        "root_ancestor_alias",
        "source_alias",
        "ancestor_alias",
        "pin_alias",
        "source_directory",
        "missing",
    ],
)
def test_native_source_aliases_and_missing_members_are_refused(
    original_source: Path, failure: str
) -> None:
    """Reject symlink roots, ancestors and members together with missing or directory inputs."""
    source = original_source / str(specification(original_source, "wri")["path"])
    if failure in {"root_alias", "root_ancestor_alias"}:
        alias = original_source.parent / "alias"
        alias.symlink_to(
            original_source if failure == "root_alias" else original_source.parent,
            target_is_directory=True,
        )
        root = alias if failure == "root_alias" else alias / original_source.name
    else:
        root = original_source
        selected = original_source / PINS if failure == "pin_alias" else source
        if failure == "ancestor_alias":
            directory = source.parent
            renamed = directory.with_name("actual-wri")
            directory.rename(renamed)
            directory.symlink_to(renamed, target_is_directory=True)
        elif failure in {"source_alias", "pin_alias"}:
            renamed = selected.with_suffix(selected.suffix + ".original")
            selected.rename(renamed)
            selected.symlink_to(renamed)
        else:
            selected.rename(selected.with_suffix(".unavailable"))
            if failure == "source_directory":
                selected.mkdir()
    with pytest.raises(ValueError):
        project(root)


@pytest.mark.parametrize(
    "failure",
    [
        "object",
        "array",
        "records_object",
        "record_scalar",
        "bool_count",
        "wrong_count",
        "feature_object",
        "attributes_array",
        "bad_json",
        "wide_csv",
        "short_csv",
        "too_large",
    ],
)
def test_damaged_native_envelopes_never_create_partial_projection(
    original_source: Path, failure: str
) -> None:
    """Reject malformed source envelopes, wrong row widths and oversized source bytes."""
    key = "agstar-Mixed"
    body = document(original_source / str(specification(original_source, key)["path"]))
    if failure == "object":
        replacement: object = 7
    elif failure == "array":
        replacement = []
    elif failure == "records_object":
        body["records"] = {}
        replacement = body
    elif failure == "record_scalar":
        rows = original_rows(body["records"])
        body["records"] = [*rows[:-1], 7]
        replacement = body
    elif failure in {"bool_count", "wrong_count"}:
        body["count"] = True if failure == "bool_count" else 8
        replacement = body
    elif failure in {"feature_object", "attributes_array"}:
        key = "br-epe-biomethane"
        body = document(original_source / str(specification(original_source, key)["path"]))
        if failure == "feature_object":
            body["features"] = {}
        else:
            original_rows(body["features"])[0]["attributes"] = []
        replacement = body
    else:
        key = "wri"
        path = original_source / str(specification(original_source, key)["path"])
        if failure == "too_large":
            with path.open("r+b") as stream:
                stream.truncate(MAX_SOURCE_BYTES + 1)
            with pytest.raises(ValueError, match="bounded"):
                project(original_source)
            return
        if failure == "bad_json":
            key = "agstar-Mixed"
            damaged = b"{"
        else:
            lines = path.read_bytes().splitlines(keepends=True)
            lines[1] = (
                (lines[1].rstrip(b"\r\n") + b",unexpected\n")
                if failure == "wide_csv"
                else b"incomplete,row\n"
            )
            damaged = b"".join(lines)
        replace_input(original_source, key, damaged)
        with pytest.raises(ValueError):
            project(original_source)
        return
    replace_input(original_source, key, json.dumps(replacement).encode())
    with pytest.raises(ValueError):
        project(original_source)
