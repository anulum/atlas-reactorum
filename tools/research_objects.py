# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — unknown JSON containers for typed research consumers.
"""Admit research object containers while retaining every original field and unknown value."""

from __future__ import annotations


def object_fields(value: object) -> dict[str, object]:
    """Read a string-keyed JSON object without inferring the types of its values.

    Parameters
    ----------
    value : object
        Original container from the validated public comparison or retained manifest.

    Returns
    -------
    dict of str to object
        A new mapping retaining all original values; the input is unchanged.

    Raises
    ------
    ValueError
        The container is not a mapping or has a non-string key.

    Notes
    -----
    Container admission is not source, scientific or rights validation. Those
    obligations remain with the public reader and separately retained hashes.
    """
    if not isinstance(value, dict):
        raise ValueError("Research object must be a mapping")
    fields: dict[str, object] = {}
    for key, item in value.items():
        field: object = key
        original: object = item
        if not isinstance(field, str):
            raise ValueError("Research object keys must be strings")
        fields[field] = original
    return fields


def object_rows(value: object) -> list[dict[str, object]]:
    """Read an ordered JSON object array without dropping fields or unknown cells.

    Parameters
    ----------
    value : object
        Original profile, source, claim or parameter collection from the public reader.

    Returns
    -------
    list of dict
        Ordered complete object rows; nested values retain their original identity.

    Raises
    ------
    ValueError
        The container is not an array or any row fails object admission.
    """
    if not isinstance(value, list):
        raise ValueError("Research rows must be an array")
    rows: list[dict[str, object]] = []
    for item in value:
        original: object = item
        rows.append(object_fields(original))
    return rows
