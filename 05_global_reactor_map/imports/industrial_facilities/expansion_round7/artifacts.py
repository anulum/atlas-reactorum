# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — deterministic industrial source artifacts
"""Render and verify capture-bound tables, attribution and complete bundle hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .build_dataset import table_bytes
from .capture import BASE_URLS
from .contracts import (
    FIELDS,
    MAX_BYTES,
    SNAPSHOT_FIELDS,
    ImportRefused,
    object_rows,
    read_json,
    read_table,
)
from .provenance import GRANTS, check_manifest, receipt_date
from .records import EXPECTED, SOURCE_URLS, project_rows

SNAPSHOT_NAME = "selected_source_snapshot.tsv"
DATASET_NAME = "industrial_facilities_round7.tsv"
SOURCE_MANIFEST = "source_manifest.json"
BUNDLE_MANIFEST = "bundle_manifest.json"
REGISTRY_FIELDS = "source_id title url publisher role license retrieved notes".split()
CAPTURE_FIELDS = "capture_name source_id origin_url retrieved bytes sha256".split()
DATA_LICENSE = "CC-BY-4.0 AND LicenseRef-opendata-swiss-terms-by"

RIGHTS_HEADER = (
    "<!--\n"
    "SPDX-License-"  # Separate the generated tag from this file licence.
    "Identifier: AGPL-3.0-or-later\n"
    "Commercial license available\n"
    "\N{COPYRIGHT SIGN} Concepts 1996–2026 Miroslav Šotek. All rights reserved.\n"
    "\N{COPYRIGHT SIGN} Code 2020–2026 Miroslav Šotek. All rights reserved.\n"
    "ORCID: 0009-0009-3560-0851\n"
    "Contact: www.anulum.li | protoscience@anulum.li\n"
    "Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round7/RIGHTS.md\n"
    "-->\n\n"
)


def json_bytes(value: object) -> bytes:
    """Encode portable manifests with deterministic keys and UTF-8 text.

    Parameters
    ----------
    value : object
        Complete validated manifest or bundle hash inventory.

    Returns
    -------
    bytes
        Canonical sorted-key JSON and final LF.
    """
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def expected_artifacts(
    snapshot: bytes,
    manifest: dict[str, object],
    observations: list[dict[str, str]],
    *,
    schema_version: int = 2,
) -> dict[str, bytes]:
    """Render every artifact from a complete capture-bound snapshot.

    Parameters
    ----------
    snapshot : bytes
        Original canonical snapshot, never rewritten.
    manifest : dict of str to object
        Reviewed primary grants and every original receipt binding.
    observations : list of dict
        Every original snapshot cell.
    schema_version : int
        Exact bundle contract: one retains the original report; two includes
        its hidden repository provenance. Source and grant bytes are identical.

    Returns
    -------
    dict of str to bytes
        Six bound artifacts followed by the complete bundle hash inventory.

    Raises
    ------
    ImportRefused
        Source observations, provenance or the bundle version is unsupported.
    """
    if type(schema_version) is not int or schema_version not in (1, 2):
        raise ImportRefused("bundle schema version is unsupported")
    check_manifest(manifest, snapshot, observations)
    captures = object_rows(manifest["captures"])
    dates = {row["source"]: row["retrieved"] for row in observations}
    captured = {str(receipt["name"]): receipt for receipt in captures}
    registry: list[dict[str, str]] = []
    publishers = {
        "ch-sfoe-biogas": "Swiss Federal Office of Energy (SFOE)",
        "it-arpae-biogas": "ARPAE Emilia-Romagna",
    }
    titles = {"ch-sfoe-biogas": "Biogas plants", "it-arpae-biogas": "Impianti a Bioenergie"}
    for source in EXPECTED:
        registry.append(
            dict(
                zip(
                    REGISTRY_FIELDS,
                    [
                        source,
                        titles[source],
                        SOURCE_URLS[source],
                        publishers[source],
                        "official_dataset",
                        GRANTS[source]["license"],
                        dates[source],
                        "Full source identities and selected original cells; facility discovery, not vessel verification.",
                    ],
                    strict=True,
                )
            )
        )
        name = "SFOE_METADATA.json" if source == "ch-sfoe-biogas" else "ARPAE_METADATA.json"
        registry.append(
            dict(
                zip(
                    REGISTRY_FIELDS,
                    [
                        source + "-grant",
                        titles[source] + " exact-resource grant",
                        BASE_URLS[name],
                        publishers[source],
                        "source_specific_grant",
                        GRANTS[source]["license"],
                        receipt_date(captured[name]["retrieved_utc"]),
                        "Exact resource "
                        + GRANTS[source]["resource_id"]
                        + "; evidence URL/hash retained, original catalogue text not redistributed.",
                    ],
                    strict=True,
                )
            )
        )
    registry.append(
        dict(
            zip(
                REGISTRY_FIELDS,
                [
                    "ch-sfoe-terms",
                    "opendata.swiss terms_by",
                    BASE_URLS["SFOE_TERMS.html"],
                    "opendata.swiss",
                    "rights_definition",
                    GRANTS["ch-sfoe-biogas"]["license"],
                    receipt_date(captured["SFOE_TERMS.html"]["retrieved_utc"]),
                    "Exact reviewed HTML SHA in source_manifest.json; terms HTML is not redistributed.",
                ],
                strict=True,
            )
        )
    )
    capture_rows = [
        dict(
            zip(
                CAPTURE_FIELDS,
                [
                    str(receipt["name"]),
                    "ch-sfoe-biogas"
                    if str(receipt["name"]).startswith("SFOE_")
                    else "it-arpae-biogas",
                    str(receipt["origin_url"]),
                    str(receipt["retrieved_utc"]),
                    str(receipt["bytes"]),
                    str(receipt["sha256"]),
                ],
                strict=True,
            )
        )
        for receipt in captures
    ]
    rights = (
        "# Industrial round 7 source rights and attribution\n\n"
        "Code uses AGPL-3.0-or-later; the imported data retain their separate upstream terms.\n"
        "The mixed source snapshot and discovery table retain both " + DATA_LICENSE + ".\n\n"
    )
    for source in EXPECTED:
        grant = GRANTS[source]
        rights += (
            f"## {publishers[source]}\n\n"
            f"Dataset: {titles[source]}. Retrieved {dates[source]}.\n"
            f"Exact resource: {grant['resource_id']} at {grant['resource_url']}.\n"
            f"Dataset licence: {grant['license']}; authoritative terms: {grant['terms_url']}.\n"
            "Adaptations: complete source selection, original-cell snapshot and consumer-field projection.\n"
            "No publisher endorsement or independently verified reactor design is implied.\n\n"
        )
    rights += (
        "The grant binding was checked against the complete original catalogue captures and "
        "the exact Swiss terms HTML hash recorded in source_manifest.json.\n"
        "Catalogue text, terms HTML, source-model PDF and cover media are not included in this bundle.\n"
        "Licence evidence for these exact datasets does not license unrelated source media.\n"
        "An offline hash check binds the reviewed artifacts; verifying against original custody "
        "additionally requires the complete captured resources and receipts.\n"
    )
    if schema_version == 2:
        rights = RIGHTS_HEADER + rights
    artifacts = {
        SNAPSHOT_NAME: snapshot,
        SOURCE_MANIFEST: json_bytes(manifest),
        DATASET_NAME: table_bytes(FIELDS, project_rows(observations)),
        "source_registry.tsv": table_bytes(REGISTRY_FIELDS, registry),
        "source_snapshot_manifest.tsv": table_bytes(CAPTURE_FIELDS, capture_rows),
        "RIGHTS.md": rights.encode("utf-8"),
    }
    inventory = {
        "schema_version": schema_version,
        "selected_counts": EXPECTED.copy(),
        "files": {
            name: {
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "license": "AGPL-3.0-or-later" if name == "RIGHTS.md" else DATA_LICENSE,
            }
            for name, body in artifacts.items()
        },
    }
    artifacts[BUNDLE_MANIFEST] = json_bytes(inventory)
    return artifacts


def bundle_schema_version(directory: Path) -> int:
    """Read the exact supported version of a bounded bundle inventory.

    Parameters
    ----------
    directory : pathlib.Path
        Frozen source bundle whose inventory is read without changing inputs.

    Returns
    -------
    int
        One for the original report or two for hidden repository provenance.

    Raises
    ------
    ImportRefused
        The inventory is missing, nonregular, malformed or has an unsupported
        version, including boolean and numeric approximations.
    """
    version = read_json(directory / BUNDLE_MANIFEST).get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ImportRefused("bundle schema version is unsupported")
    return version


def read_bundle(directory: Path) -> tuple[bytes, dict[str, object], list[dict[str, str]]]:
    """Verify every artifact and completion inventory without writing inputs.

    Parameters
    ----------
    directory : pathlib.Path
        Existing complete frozen source bundle.

    Returns
    -------
    tuple
        Original snapshot bytes, verified provenance and all original cells.

    Raises
    ------
    ImportRefused
        The version is unsupported or a bounded file or exact byte binding differs.
    OSError
        A requested artifact cannot be read.
    """
    observations = read_table(directory / SNAPSHOT_NAME, SNAPSHOT_FIELDS)
    snapshot = (directory / SNAPSHOT_NAME).read_bytes()
    manifest = read_json(directory / SOURCE_MANIFEST)
    version = bundle_schema_version(directory)
    for name, body in expected_artifacts(
        snapshot, manifest, observations, schema_version=version
    ).items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ImportRefused("bundle artifact must be a bounded regular file")
        if path.read_bytes() != body:
            raise ImportRefused("bundle artifact differs from its full source/rights/hash binding")
    return snapshot, manifest, observations
