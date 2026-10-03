# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB visible data selection

"""Select source dictionaries and complete visible panes without the renderer."""

from __future__ import annotations

from datetime import date

from .framing import decode_frames, encode_frames
from .reader import PROJECTION_KIND, SOURCE_URL, parse_dashboard
from .values import DashboardRefused, descend, object_list, object_map

DICTIONARY_PATH = (
    "dataDictionary",
    "presModelHolder",
    "genDataDictionaryPresModel",
    "dataSegments",
    "0",
    "dataColumns",
)
VIEWS_PATH = (
    "vizData",
    "presModelHolder",
    "genPresModelMapPresModel",
    "presModelMap",
)
PANE_PATH = ("presModelHolder", "genVizDataPresModel", "paneColumnsData")


def _pane(view: object) -> dict[str, object]:
    pane = object_map(descend(view, PANE_PATH))
    columns = object_list(descend(pane, ("paneColumnsList",)))
    source_columns = object_list(descend(columns[0], ("vizPaneColumns",)))
    selected_columns = [
        {"tupleIds": descend(source_columns[0], ("tupleIds",))},
        *[
            {key: descend(column, (key,)) for key in ("valueIndices", "aliasIndices")}
            for column in source_columns[1:]
        ],
    ]
    metadata = object_list(descend(pane, ("vizDataColumns",)))
    selected_metadata = [
        {"columnIndices": descend(metadata[0], ("columnIndices",))},
        *[
            {
                key: descend(column, (key,))
                for key in ("fieldCaption", "dataType", "paneIndices", "columnIndices")
            }
            for column in metadata[1:]
        ],
    ]
    return {
        "presModelHolder": {
            "genVizDataPresModel": {
                "paneColumnsData": {
                    "paneColumnsList": [{"vizPaneColumns": selected_columns}],
                    "vizDataColumns": selected_metadata,
                }
            }
        }
    }


def select_visible_data(payload: bytes, retrieved_date: str) -> bytes:
    """Project every source cell needed by the complete Table and Main views.

    Parameters
    ----------
    payload : bytes
        Original ordinary response or a previously labelled selection. Values
        come directly from its dictionaries and panes, never a derived TSV.
    retrieved_date : str
        Actual acquisition date, in canonical ISO calendar form. Reselection
        preserves the existing original-response identity and date.

    Returns
    -------
    bytes
        Authored projection header and selected source-data frame. Dictionary
        types, members, tuple positions and raw/display indices stay unchanged.

    Raises
    ------
    DashboardRefused
        If the complete source views or acquisition date cannot be validated.
    """
    dashboard = parse_dashboard(payload)
    try:
        checked = date.fromisoformat(retrieved_date)
    except ValueError:
        raise DashboardRefused("FFDB retrieval date must be an ISO calendar date.") from None
    if checked.isoformat() != retrieved_date:
        raise DashboardRefused("FFDB retrieval date must be an ISO calendar date.")
    if dashboard.retrieved_date is not None and dashboard.retrieved_date != retrieved_date:
        raise DashboardRefused("FFDB selection acquisition date cannot be changed.")
    secondary = object_map(descend(decode_frames(payload)[1], ("secondaryInfo", "presModelMap")))
    dictionaries = [
        {key: descend(column, (key,)) for key in ("dataType", "dataValues")}
        for column in object_list(descend(secondary, DICTIONARY_PATH))
    ]
    views = object_map(descend(secondary, VIEWS_PATH))
    selected = {
        "dataDictionary": {
            "presModelHolder": {
                "genDataDictionaryPresModel": {"dataSegments": {"0": {"dataColumns": dictionaries}}}
            }
        },
        "vizData": {
            "presModelHolder": {
                "genPresModelMapPresModel": {
                    "presModelMap": {
                        name: _pane(descend(views, (name,))) for name in ("Table", "Main")
                    }
                }
            }
        },
    }
    return encode_frames(
        [
            {
                "atlas_projection": {
                    "schema_version": 1,
                    "kind": PROJECTION_KIND,
                    "source_url": SOURCE_URL,
                    "original_response_sha256": dashboard.original_response_sha256,
                    "retrieved_date": retrieved_date,
                }
            },
            {"secondaryInfo": {"presModelMap": selected}},
        ]
    )
