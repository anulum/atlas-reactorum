# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual fusion layer test copies

"""Provide isolated native layouts made from the actual public compilation selection and complete overlay layers."""

from __future__ import annotations

import shutil
from pathlib import Path

from ._catalogue_inputs import ROOT

DIRECTORY = ROOT / "05_global_reactor_map/imports/fusion"


def copy_fusion_layers(destination: Path) -> Path:
    """Copy the actual base and all overlay/source TSVs without copying executable code."""
    for name in ("fusion_facilities.tsv", "source_registry.tsv"):
        shutil.copy2(DIRECTORY / name, destination / name)
    for name in ("enrichment", "enrichment_round2", "enrichment_round3"):
        target = destination / name
        target.mkdir()
        for source in (DIRECTORY / name).glob("*.tsv"):
            shutil.copy2(source, target / source.name)
    return destination
