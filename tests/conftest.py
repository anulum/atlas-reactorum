# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tests/conftest.py

"""Shared fixtures for the Atlas Reactorum test suite.

The suite loads the modules that actually build the published datasets, and
the published datasets themselves, rather than fixtures that merely resemble
them. A test that passes against a hand-made fixture but would fail against
the real registry is worse than no test.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The suite runs build scripts as real processes. Coverage only follows into a
# subprocess when this variable names the configuration file, so it is set for
# every child the tests spawn.
os.environ.setdefault("COVERAGE_PROCESS_START", str(ROOT / "pyproject.toml"))
DATA = ROOT / "04_interactive_presentation" / "data"


def _records(document: Any) -> list[dict[str, Any]]:
    """Return the record list from a dataset document.

    Parameters
    ----------
    document : Any
        A parsed dataset, either the wrapped object form or a bare array.

    Returns
    -------
    list of dict
        The records it carries.
    """
    if isinstance(document, dict):
        wrapped: list[dict[str, Any]] = document["records"]
        return wrapped
    bare: list[dict[str, Any]] = document
    return bare


def load_module(relative_path: str, name: str) -> ModuleType:
    """Import a build script by path, without executing its entry point.

    The build scripts are standalone files rather than an installed package,
    so they are loaded through the import machinery directly. Each guards its
    work behind ``if __name__ == "__main__"``, so importing one runs no build.

    Parameters
    ----------
    relative_path : str
        Path to the script, relative to the repository root.
    name : str
        Module name to register the import under.

    Returns
    -------
    types.ModuleType
        The imported module.
    """
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def build_datasets() -> ModuleType:
    """Return the module that assembles every dataset the atlas loads."""
    return load_module(
        "04_interactive_presentation/scripts/build_datasets.py", "atlas_build_datasets"
    )


@pytest.fixture(scope="session")
def build_coverage() -> ModuleType:
    """Return the module that generates the field-completeness snapshot."""
    return load_module("metadata/coverage_audit/build_coverage.py", "atlas_build_coverage")


@pytest.fixture(scope="session")
def facilities() -> list[dict[str, Any]]:
    """Return every published facility record."""
    return _records(json.loads((DATA / "global_reactors.sample.json").read_text(encoding="utf-8")))


@pytest.fixture(scope="session")
def companies() -> list[dict[str, Any]]:
    """Return every published company and programme record."""
    return _records(json.loads((DATA / "fusion_companies.sample.json").read_text(encoding="utf-8")))


@pytest.fixture(scope="session")
def facility_schema() -> dict[str, Any]:
    """Return the published JSON schema for facility records."""
    schema: dict[str, Any] = json.loads(
        (DATA / "global_reactors.schema.json").read_text(encoding="utf-8")
    )
    return schema


@pytest.fixture(scope="session")
def company_schema() -> dict[str, Any]:
    """Return the published JSON schema for company records."""
    schema: dict[str, Any] = json.loads(
        (DATA / "fusion_companies.schema.json").read_text(encoding="utf-8")
    )
    return schema
