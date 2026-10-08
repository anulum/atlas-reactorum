# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility-field native producer conformance

"""Exercise the real native CLI and atomic external publication boundary."""

from __future__ import annotations

import ctypes
import json
import os
import select
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from metadata.facility_fields.build import build

from ._facility_field_sources import PINS, ROOT, document, run_cli
from ._facility_field_sources import original_source as original_source


@pytest.mark.parametrize("optimize", [False, True])
def test_native_producer_rebuilds_complete_original_assertions(
    original_source: Path, optimize: bool
) -> None:
    """Rebuild exactly 1,631 assertions through CLI and API without leaving temporary output."""
    output = original_source.parent / "native.json"
    result = run_cli("build", original_source, "--output", str(output), optimize=optimize)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1631 original field assertions written" in result.stdout
    assert document(output)["record_count"] == 1631
    second = original_source.parent / "second.json"
    assert build(original_source, second) == 1631
    assert second.read_bytes() == output.read_bytes()
    assert not list(output.parent.glob(".facility-fields-*"))


@pytest.mark.parametrize(
    "failure",
    [
        "existing",
        "directory",
        "source",
        "repository",
        "alias",
        "dangling",
        "ancestor_alias",
        "missing_parent",
        "file_parent",
        "hardlink",
    ],
)
@pytest.mark.parametrize("optimize", [False, True])
def test_native_destination_refusals_preserve_complete_inputs(
    original_source: Path, failure: str, optimize: bool
) -> None:
    """Refuse protected or invalid destinations in both CLI modes while preserving input bytes."""
    output = original_source.parent / "output.json"
    source = original_source / "metadata/facility_fields/source_pins.json"
    if failure == "existing":
        output.write_bytes(b"existing owner bytes")
    elif failure == "directory":
        output.mkdir()
    elif failure == "source":
        output = source
    elif failure == "repository":
        output = ROOT / "metadata/facility_fields/must-not-exist.json"
    elif failure in {"alias", "dangling"}:
        output.symlink_to(source if failure == "alias" else output.with_name("missing"))
    elif failure == "ancestor_alias":
        parent = original_source.parent / "alias"
        parent.symlink_to(original_source.parent, target_is_directory=True)
        output = parent / "output.json"
    elif failure == "missing_parent":
        output = original_source.parent / "missing/output.json"
    elif failure == "file_parent":
        output = source / "output.json"
    elif failure == "hardlink":
        os.link(source, output)
    before = source.read_bytes()
    existing = output.read_bytes() if output.is_file() else None
    result = run_cli("build", original_source, "--output", str(output), optimize=optimize)
    assert result.returncode == 1
    assert (
        result.stdout.strip()
        == "FACILITY FIELD BUILD FAILED: complete source or protected destination differs"
    )
    assert "Traceback" not in result.stderr
    assert source.read_bytes() == before
    if existing is not None:
        assert output.read_bytes() == existing
    assert not list(original_source.parent.glob(".facility-fields-*"))


@pytest.mark.parametrize("optimize", [False, True])
def test_native_partial_input_refusal_leaves_no_output(
    original_source: Path, optimize: bool
) -> None:
    """Refuse a missing native source member without publishing partial or temporary output."""
    path = original_source / "tests/data/industrial_base/Dairy.json"
    path.rename(path.with_suffix(".unavailable"))
    output = original_source.parent / "output.json"
    result = run_cli("build", original_source, "--output", str(output), optimize=optimize)
    assert result.returncode == 1
    assert not output.exists()
    assert not list(output.parent.glob(".facility-fields-*"))


def test_original_pin_change_during_native_io_refuses_publication(original_source: Path) -> None:
    """Observe actual source opening and reject changed pins before publishing any output."""
    library = ctypes.CDLL(None, use_errno=True)
    library.inotify_init1.argtypes = [ctypes.c_int]
    library.inotify_init1.restype = ctypes.c_int
    library.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    library.inotify_add_watch.restype = ctypes.c_int
    descriptor = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    assert descriptor >= 0
    output = original_source.parent / "must-not-publish.json"
    pins = original_source / PINS
    reviewed = document(pins)
    try:
        source = original_source / "tests/data/wri_gppd/nuclear_and_filter_control.csv"
        assert library.inotify_add_watch(descriptor, os.fsencode(source), 0x20) >= 0
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(build, original_source, output)
            ready, _, _ = select.select([descriptor], [], [], 5)
            assert ready, "complete native WRI input was not opened"
            assert os.read(descriptor, 4096)
            pins.write_text(json.dumps(reviewed, ensure_ascii=False, indent=3) + "\n")
            with pytest.raises(ValueError, match="pins changed"):
                pending.result(timeout=5)
    finally:
        os.close(descriptor)
    assert not output.exists()
    assert not list(output.parent.glob(".facility-fields-*"))
