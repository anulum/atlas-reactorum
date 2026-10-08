# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native IPython startup coverage for original notebook cells.
"""Retain actual kernel arcs and the native compiler's cached source without replacing compilation."""

from __future__ import annotations

import atexit
import dis
import hashlib
import json
import linecache
import os
import sys
from pathlib import Path
from types import FrameType

import coverage


def start_coverage() -> None:
    """Trace native cell filenames and retain their complete cached source at kernel exit.

    Raises
    ------
    RuntimeError
        A measured native cell has no compiler-cached source.

    Notes
    -----
    Only the owning test's IPython startup directory executes this module.
    The native compiler, frame boundaries and cell contents are unchanged.
    """
    cov = coverage.Coverage(
        branch=True,
        data_file=os.environ["ATLAS_CELL_COVERAGE"],
        include=[str(Path(os.environ["TMPDIR"]) / "ipykernel_*/*.py")],
        config_file=False,
    )
    cov.start()
    frames: dict[str, list[dict[str, object]]] = {}

    def record_frame(frame: FrameType, event: str, arg: object) -> None:
        """Retain actual compiled instructions when a native cell frame is entered."""
        filename = frame.f_code.co_filename
        if event != "call" or not filename.startswith(os.environ["TMPDIR"] + "/ipykernel_"):
            return
        frames.setdefault(filename, []).append(
            {
                "name": frame.f_code.co_name,
                "first_line": frame.f_code.co_firstlineno,
                "instructions": [
                    {
                        "offset": item.offset,
                        "opname": item.opname,
                        "line": item.positions.lineno if item.positions is not None else None,
                    }
                    for item in dis.get_instructions(frame.f_code)
                ],
            }
        )

    if sys.getprofile() is not None:
        raise RuntimeError("Kernel already has a native frame profiler")
    sys.setprofile(record_frame)

    def finish() -> None:
        """Save native arcs and complete compiler-cached source before the kernel exits."""
        sys.setprofile(None)
        cov.stop()
        cov.save()
        bindings = []
        for filename in sorted(cov.get_data().measured_files()):
            text = "".join(linecache.getlines(filename))
            if not text:
                raise RuntimeError("Native compiler source unavailable")
            source = Path(filename)
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(text, encoding="utf-8")
            bindings.append(
                {
                    "filename": filename,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "text": text,
                    "entered_native_frames": frames.get(filename, []),
                }
            )
        Path(os.environ["ATLAS_CELL_BINDINGS"]).write_text(
            json.dumps(bindings, indent=2), encoding="utf-8"
        )

    atexit.register(finish)


if os.environ.get("ATLAS_CELL_COVERAGE"):
    start_coverage()
