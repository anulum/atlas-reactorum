# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — locked native notebook source and complete kernel execution.
"""Admit native notebook schema, portable Python cells and source-exact execution results."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from importlib.metadata import distribution, version
from pathlib import Path
from typing import cast

from jsonschema import Draft4Validator, FormatChecker

from tools.research_objects import object_fields, object_rows

PINS = {
    "ruff": "0.16.9",
    "mypy": "2.3.1",
    "nbqa": "1.9.1",
    "nbclient": "0.11.0",
    "nbformat": "5.11.1",
    "ipykernel": "7.4.0",
}


def cell_source(cell: dict[str, object]) -> str:
    """Read complete native-schema-admitted cell text without changing its original values.

    Parameters
    ----------
    cell : dict of str to object
        Original cell after native schema admission; source is text or a list of text segments.

    Returns
    -------
    str
        Exact concatenated original text, preserving whitespace, order and content.
    """
    source = cell["source"]
    return source if isinstance(source, str) else "".join(cast(list[str], source))


def cells(source: bytes) -> list[dict[str, object]]:
    """Validate the native format schema and admit every executable Python cell.

    Parameters
    ----------
    source : bytes
        Complete original notebook JSON, including metadata and all cells.

    Returns
    -------
    list of dict
        Complete ordered cells with no skipped code or silently converted language.

    Raises
    ------
    ValueError
        The notebook is not Python or declares skipped/empty executable cells.
    SyntaxError
        A code cell is not ordinary valid Python, including unsupported kernel magics.
    jsonschema.ValidationError
        The original format fails the installed native notebook schema.
    """
    value: object = json.loads(source)
    document = object_fields(value)
    schema_path = Path(
        str(distribution("nbformat").locate_file("nbformat/v4/nbformat.v4.5.schema.json"))
    )
    schema = object_fields(json.loads(schema_path.read_text()))
    Draft4Validator(schema, format_checker=FormatChecker()).validate(document)
    metadata = object_fields(document["metadata"])
    if object_fields(metadata["kernelspec"])["language"] != "python":
        raise ValueError("Notebook language needs its own qualified native gate")
    original_cells = object_rows(document["cells"])
    count = 0
    for cell in original_cells:
        if cell["cell_type"] != "code":
            continue
        tags = cast(list[str], object_fields(cell["metadata"]).get("tags", []))
        if "skip-execution" in tags:
            raise ValueError("Notebook code cells must not be skipped")
        text = cell_source(cell)
        if not text.strip():
            raise ValueError("Notebook code cell is empty")
        ast.parse(text)
        count += 1
    if not count:
        raise ValueError("Notebook has no executable Python cells")
    return original_cells


def verify(source: bytes, executed: bytes | None = None) -> dict[str, object]:
    """Qualify original cells and their optional complete native kernel result.

    Parameters
    ----------
    source : bytes
        Complete original notebook, before native source checks and execution.
    executed : bytes or None
        Full output from the actual Jupyter CLI; None checks source admission only.

    Returns
    -------
    dict of str to object
        Source digest, executed-code count and original kernel stdout, after complete admission.

    Raises
    ------
    ValueError
        A locked native tool differs, cell source or type changed, or a code cell was not executed.
    """
    for name, expected in PINS.items():
        if version(name) != expected:
            raise ValueError("Notebook native tool version mismatch: " + name)
    original_cells = cells(source)
    count = 0
    stdout: list[str] = []
    if executed is not None:
        completed = cells(executed)
        if [(cell["cell_type"], cell_source(cell)) for cell in completed] != [
            (cell["cell_type"], cell_source(cell)) for cell in original_cells
        ]:
            raise ValueError("Notebook kernel changed cell sources or types")
        for cell in completed:
            if cell["cell_type"] != "code":
                continue
            if not isinstance(cell["execution_count"], int):
                raise ValueError("Notebook kernel did not execute every code cell")
            for output in object_rows(cell["outputs"]):
                if output["output_type"] == "stream" and output["name"] == "stdout":
                    text = output["text"]
                    stdout.append(text if isinstance(text, str) else "".join(cast(list[str], text)))
                if output["output_type"] == "error":
                    raise ValueError("Notebook kernel returned an error")
            count += 1
    return {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "executed_code_cells": count,
        "execution_stdout": "".join(stdout),
    }


def main(argv: list[str] | None = None) -> int:
    """Admit one original notebook and its optional native execution result.

    Parameters
    ----------
    argv : list of str or None
        Explicit original path and optional executed path; None uses native process arguments.

    Returns
    -------
    int
        Zero after admission; schema, source or execution errors propagate as failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--executed", type=Path)
    args = parser.parse_args(argv)
    result = verify(args.source.read_bytes(), args.executed.read_bytes() if args.executed else None)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
