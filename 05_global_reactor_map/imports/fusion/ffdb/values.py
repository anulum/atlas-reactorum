# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — typed FFDB source values

"""Validate publisher JSON values before interpreting visible dashboard cells."""

from __future__ import annotations

import math
from typing import cast


class DashboardRefused(ValueError):
    """Report a deliberately authored refusal of a malformed FFDB source."""


def object_map(value: object) -> dict[str, object]:
    """Require a JSON object with string keys.

    Parameters
    ----------
    value : object
        Decoded source value, whose structure has not yet been checked.

    Returns
    -------
    dict of str to object
        The original mapping, without conversion or omitted members.

    Raises
    ------
    DashboardRefused
        If the value is not an object with string keys.
    """
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise DashboardRefused("FFDB source requires a JSON object.")
    return cast(dict[str, object], value)


def object_list(value: object) -> list[object]:
    """Require a JSON array without coercing its members.

    Parameters
    ----------
    value : object
        Source value at an array position.

    Returns
    -------
    list of object
        The original array for subsequent member validation.

    Raises
    ------
    DashboardRefused
        If the value is not an array.
    """
    if not isinstance(value, list):
        raise DashboardRefused("FFDB source requires a JSON array.")
    return cast(list[object], value)


def integer(value: object) -> int:
    """Require an integer index, excluding JSON booleans.

    Parameters
    ----------
    value : object
        Tuple, pane or dictionary index from the source.

    Returns
    -------
    int
        The original integer.

    Raises
    ------
    DashboardRefused
        If the value is boolean or has a noninteger type.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise DashboardRefused("FFDB source requires an integer index.")
    return value


def text(value: object) -> str:
    """Require source text without stripping, case folding or normalisation.

    Parameters
    ----------
    value : object
        Publisher value to retain verbatim.

    Returns
    -------
    str
        The original text.

    Raises
    ------
    DashboardRefused
        If the value is not text.
    """
    if not isinstance(value, str):
        raise DashboardRefused("FFDB source requires a text value.")
    return value


def number(value: object) -> int | float:
    """Require a finite numeric value, excluding JSON booleans.

    Parameters
    ----------
    value : object
        Publisher coordinate or numeric dictionary member.

    Returns
    -------
    int or float
        The original number with its decoded type preserved.

    Raises
    ------
    DashboardRefused
        If the value is nonnumeric, boolean or nonfinite.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DashboardRefused("FFDB source requires a finite numeric value.")
    if isinstance(value, float) and not math.isfinite(value):
        raise DashboardRefused("FFDB source requires a finite numeric value.")
    return value


def descend(value: object, keys: tuple[str, ...]) -> object:
    """Follow the exact publisher object path, refusing missing members.

    Parameters
    ----------
    value : object
        Source object at the beginning of the path.
    keys : tuple of str
        Required member names in traversal order.

    Returns
    -------
    object
        The member at the end of the path, still requiring value validation.

    Raises
    ------
    DashboardRefused
        If a required object member is missing or wrongly typed.
    """
    for key in keys:
        mapping = object_map(value)
        if key not in mapping:
            raise DashboardRefused("FFDB source is missing a required member.")
        value = mapping[key]
    return value
