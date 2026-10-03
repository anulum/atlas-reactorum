#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — historical fusion acquisition boundary

"""Refuse the former live acquisition command.

The original collector is preserved in private acquisition custody. Frozen
historical integration remains available in the presentation builder; the
supported default uses pinned FFDB data without contacting a publisher.
"""

from __future__ import annotations

import sys

REFUSAL = "Historical FusionBenchmark live acquisition is not approved; use the pinned FFDB build."


class HistoricalAcquisitionRefused(ValueError):
    """The historical importer is not approved for new collection."""


def fetch(url: str) -> bytes:
    """Refuse every live request without opening a protocol.

    Parameters
    ----------
    url : str
        Requested source reference; no network or local-file request is made.

    Raises
    ------
    HistoricalAcquisitionRefused
        Always. The retained historical data are not a live-refresh grant.
    """
    raise HistoricalAcquisitionRefused(REFUSAL)


def main() -> None:
    """Refuse the historical acquisition command before any source is opened.

    Raises
    ------
    HistoricalAcquisitionRefused
        Always. Frozen-data integration is a separate presentation command.
    """
    fetch("https://fusionbenchmark.com/fusion/")


if __name__ == "__main__":
    try:
        main()
    except HistoricalAcquisitionRefused as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from None
