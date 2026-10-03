# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields source-to-field projection

"""Project published end uses, feedstocks and fuel classifications separately."""

from __future__ import annotations

from typing import TypedDict

from .inputs import NativeInput, text


class FieldObservation(TypedDict):
    """One verbatim source assertion with its exact field and dataset binding."""

    target_id: str
    target_dataset: str
    target_sha256: str
    field: str
    value: str
    basis: str
    source_record_id: str
    source_field: str
    source_artifact: str
    source_sha256: str
    source_url: str
    checked: str
    license: str


def identity(value: object) -> str:
    """Retain a native integer or text record identity.

    Parameters
    ----------
    value : object
        Native publisher identifier.

    Returns
    -------
    str
        Exact text identity or decimal integer representation.

    Raises
    ------
    ValueError
        The identifier is absent, boolean or an unsupported scalar.
    """
    if type(value) is int:
        return str(value)
    return text(value)


def observation(
    source: NativeInput,
    target: NativeInput,
    *,
    target_id: str,
    field: str,
    value: object,
    basis: str,
    record_id: str,
    source_field: str,
    source_url: str | None = None,
    checked: str | None = None,
    license_id: str | None = None,
) -> FieldObservation | None:
    """Bind one nonblank original cell without filling source absence.

    Parameters
    ----------
    source : NativeInput
        Complete original source.
    target : NativeInput
        Complete original target dataset.
    target_id, field, basis, record_id, source_field : str
        Exact target identity and reviewed source-field meaning.
    value : object
        Original source cell. None or whitespace-only text contributes nothing.
    source_url, checked, license_id : str or None
        Per-row source bindings for the mixed round-seven snapshot.

    Returns
    -------
    FieldObservation or None
        Verbatim source assertion, or no assertion for an absent original value.

    Raises
    ------
    ValueError
        A present source cell or provenance value is invalid.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return {
        "target_id": target_id,
        "target_dataset": target.path,
        "target_sha256": target.sha256,
        "field": field,
        "value": text(value),
        "basis": basis,
        "source_record_id": record_id,
        "source_field": source_field,
        "source_artifact": source.path,
        "source_sha256": source.sha256,
        "source_url": source_url if source_url is not None else text(source.metadata["url"]),
        "checked": checked if checked is not None else text(source.metadata["checked"]),
        "license": license_id if license_id is not None else text(source.metadata["license"]),
    }
