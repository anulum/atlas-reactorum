# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native full-data browser checker conformance

"""Validate unsafe protocol mutations against observations from real native Chrome."""

from __future__ import annotations

import copy
import json

import pytest

from ._catalogue_inputs import ROOT
from .browser_checks_runtime import SCRIPT, BrowserEndpoints, NativeObservation
from .browser_checks_runtime import native_browser as native_browser
from .browser_checks_runtime import native_observation as native_observation
from .conftest import load_module


@pytest.mark.parametrize(
    "damage",
    [
        "root",
        "item",
        "absent",
        "duplicate",
        "missing_debugger",
        "debugger_type",
        "remote_debugger",
        "debugger_scheme",
        "debugger_path",
        "debugger_query",
        "debugger_fragment",
    ],
)
def test_public_selection_refuses_damaged_actual_target_documents(
    native_browser: BrowserEndpoints, native_observation: NativeObservation, damage: str
) -> None:
    """Reject each unsafe target-list mutation derived from the complete native Chrome observation.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.
    native_observation : NativeObservation
        Complete target/reply/count observation captured from the actual native browser.
    damage : str
        Named corruption applied to a copy of an actual native protocol observation.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    targets = copy.deepcopy(native_observation["targets"])
    if damage == "root":
        document: object = {"records": targets}
    elif damage == "item":
        document = [*targets, None]
    else:
        document = targets
        selected = next(target for target in targets if target["url"] == native_browser["page"])
        if damage == "absent":
            selected["url"] = native_browser["page"] + "?not-the-same-page"
        elif damage == "duplicate":
            targets.append(selected.copy())
        elif damage == "missing_debugger":
            selected.pop("webSocketDebuggerUrl")
        elif damage == "debugger_type":
            selected["webSocketDebuggerUrl"] = True
        else:
            selected["webSocketDebuggerUrl"] = {
                "remote_debugger": "ws://example.org/devtools/page/identity",
                "debugger_scheme": native_browser["endpoint"].replace("http:", "wss:")
                + "/devtools/page/identity",
                "debugger_path": native_browser["endpoint"].replace("http:", "ws:")
                + "/other/identity",
                "debugger_query": native_browser["endpoint"].replace("http:", "ws:")
                + "/devtools/page/identity?x=1",
                "debugger_fragment": native_browser["endpoint"].replace("http:", "ws:")
                + "/devtools/page/identity#section",
            }[damage]
    with pytest.raises(module.BrowserCheckError):
        module.select_page(document, native_browser["page"], native_browser["endpoint"])


@pytest.mark.parametrize(
    "damage", ["root", "json", "event", "other_id", "error", "result", "exception"]
)
def test_public_decoder_uses_captured_native_reply_and_explicit_corruptions(
    native_observation: NativeObservation, damage: str
) -> None:
    """Distinguish native protocol events and unrelated replies from malformed or failed command results.

    Parameters
    ----------
    native_observation : NativeObservation
        Complete target/reply/count observation captured from the actual native browser.
    damage : str
        Named corruption applied to a copy of an actual native protocol observation.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    message = copy.deepcopy(native_observation["message"])
    if damage == "root":
        payload = json.dumps([message])
    elif damage == "json":
        payload = str(native_observation["payload"])[:-1]
    else:
        if damage == "event":
            message.pop("id")
        elif damage == "other_id":
            message["id"] = 100000
        elif damage == "error":
            message["error"] = {"code": -32601, "message": "explicit damaged replay"}
        elif damage == "result":
            message["result"] = []
        elif damage == "exception":
            result = copy.deepcopy(native_observation["result"])
            result["exceptionDetails"] = {"text": "explicit damaged replay"}
            message["result"] = result
        payload = json.dumps(message)
    if damage in {"event", "other_id"}:
        assert module.response_result(payload, 100001) is None
    else:
        with pytest.raises((module.BrowserCheckError, ValueError)):
            module.response_result(payload, 100001)


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_public_remote_value_refuses_damage_to_actual_native_descriptor(
    native_observation: NativeObservation, damage: str
) -> None:
    """Reject missing and invalid remote-object descriptors copied from a real Chrome reply.

    Parameters
    ----------
    native_observation : NativeObservation
        Complete target/reply/count observation captured from the actual native browser.
    damage : str
        Named corruption applied to a copy of an actual native protocol observation.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    result = copy.deepcopy(native_observation["result"])
    if damage == "missing":
        result.pop("result")
    else:
        result["result"] = []
    with pytest.raises(module.BrowserCheckError, match="remote object"):
        module.evaluation_value(result)


@pytest.mark.parametrize("damage", ["root", "missing", "extra", "bool", "text", "different"])
def test_public_count_decoder_refuses_corrupted_complete_native_observation(
    native_observation: NativeObservation, damage: str
) -> None:
    """Reject malformed, incomplete and changed full-catalogue counts captured through native Chrome.

    Parameters
    ----------
    native_observation : NativeObservation
        Complete target/reply/count observation captured from the actual native browser.
    damage : str
        Named corruption applied to a copy of an actual native protocol observation.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    counts = native_observation["counts"].copy()
    if damage == "root":
        observation: object = list(counts.values())
    else:
        changed: dict[str, object] = dict(counts)
        if damage == "missing":
            changed.pop("companies")
        elif damage == "extra":
            changed["untracked"] = 1
        else:
            changed["companies"] = {
                "bool": True,
                "text": str(counts["companies"]),
                "different": counts["companies"] - 1,
            }[damage]
        observation = changed
    with pytest.raises(module.BrowserCheckError, match="count"):
        module.parse_counts(observation)
