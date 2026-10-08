# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — original notebook and actual native kernel receipt admission.
"""Refuse changed/unexecuted notebook receipts and retain genuine complete kernel behavior."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import pytest
from jsonschema import ValidationError

from tools.notebooks import cells, main, verify
from tools.research_objects import object_fields, object_rows

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "examples/research/comparison.ipynb"


@pytest.fixture(scope="module")
def kernel_receipts(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, Path, Path]:
    """Produce original and deliberately failed receipts through actual locked Jupyter kernels.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Owning working-disk parent for real notebooks, kernel and captured logs.

    Returns
    -------
    tuple of pathlib.Path
        Original/executed and deliberately failing/executed notebook paths.
    """
    parent = tmp_path_factory.mktemp("notebook-native-receipts")
    source = parent / "original.ipynb"
    source.write_bytes(NOTEBOOK.read_bytes())
    failed = parent / "failed.ipynb"
    document = object_fields(json.loads(source.read_bytes()))
    original_cells = object_rows(document["cells"])
    code = next(cell for cell in original_cells if cell["cell_type"] == "code")
    code["source"] = ['raise ValueError("deliberate native kernel refusal")\n']
    document["cells"] = original_cells
    failed.write_text(json.dumps(document))
    runtime = parent / "runtime"
    runtime.mkdir()
    environment = {
        **os.environ,
        "ATLAS_REPOSITORY": str(ROOT),
        "JUPYTER_DATA_DIR": str(parent / "data"),
        "JUPYTER_CONFIG_DIR": str(parent / "config"),
        "JUPYTER_RUNTIME_DIR": str(runtime),
        "JUPYTER_PATH": str(parent / "share/jupyter"),
        "IPYTHONDIR": str(parent / "ipython"),
    }
    commands = [
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            str(parent),
            "--name",
            "atlas-admission",
        ],
        [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "--kernel_name=atlas-admission",
            "--timeout=60",
            "--startup_timeout=20",
            "--output=original-executed",
            str(source),
        ],
        [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "--kernel_name=atlas-admission",
            "--timeout=60",
            "--startup_timeout=20",
            "--allow-errors",
            "--output=failed-executed",
            str(failed),
        ],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(
            command, cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120
        )
        (parent / f"native-{index}.stdout").write_text(result.stdout)
        (parent / f"native-{index}.stderr").write_text(result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
    assert source.read_bytes() == NOTEBOOK.read_bytes()
    return source, parent / "original-executed.ipynb", failed, parent / "failed-executed.ipynb"


def test_original_source_and_genuine_complete_kernel_result(
    kernel_receipts: tuple[Path, Path, Path, Path],
) -> None:
    """Admit all five real cells and original statement/absence outputs through API and CLI.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Genuine original and failed outputs from the fixture's actual native kernels.
    """
    source, executed, _, _ = kernel_receipts
    assert verify(source.read_bytes())["executed_code_cells"] == 0
    assert verify(source.read_bytes(), executed.read_bytes())["executed_code_cells"] == 5
    assert main([str(source)]) == 0
    assert main([str(source), "--executed", str(executed)]) == 0
    document = object_fields(json.loads(executed.read_bytes()))
    streams = []
    for cell in object_rows(document["cells"]):
        if cell["cell_type"] == "code":
            for output in object_rows(cell["outputs"]):
                if output["output_type"] == "stream":
                    text = output["text"]
                    assert isinstance(text, (str, list))
                    streams.append(text if isinstance(text, str) else "".join(text))
    observed = "".join(streams)
    assert "Repeated restoration agrees: True" in observed
    assert "Original statements retained: 11" in observed
    assert "Missing numeric parameter records: 2" in observed
    assert verify(source.read_bytes(), executed.read_bytes())["execution_stdout"] == observed


def test_native_stream_text_encodings_retain_the_same_original_output(
    kernel_receipts: tuple[Path, Path, Path, Path],
) -> None:
    """Admit both native schema text encodings of genuine kernel output without changing values.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Complete original result from the real native kernel, retained without mutation.
    """
    source, executed, _, _ = kernel_receipts
    original = executed.read_bytes()
    expected = verify(source.read_bytes(), original)
    document = object_fields(json.loads(original))
    rows = object_rows(document["cells"])
    for cell in rows:
        if cell["cell_type"] == "code":
            outputs = object_rows(cell["outputs"])
            for output in outputs:
                if output["output_type"] == "stream":
                    text = output["text"]
                    assert isinstance(text, (str, list))
                    output["text"] = text if isinstance(text, str) else "".join(text)
            cell["outputs"] = outputs
    document["cells"] = rows
    assert verify(source.read_bytes(), json.dumps(document).encode()) == expected
    assert executed.read_bytes() == original


def test_real_kernel_stderr_and_display_outputs_preserve_stdout_contract(
    kernel_receipts: tuple[Path, Path, Path, Path],
) -> None:
    """Retain original stdout while a genuine kernel also emits stderr and a native display result.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Original source and owned installed kernel used for another actual public CLI execution.
    """
    original, _, _, _ = kernel_receipts
    parent = original.parent
    source = parent / "native-output-kinds.ipynb"
    document = object_fields(json.loads(original.read_bytes()))
    rows = object_rows(document["cells"])
    final = next(cell for cell in reversed(rows) if cell["cell_type"] == "code")
    text = final["source"]
    assert isinstance(text, list)
    final["source"] = [*text, '\nprint("native kernel stderr", file=sys.stderr)\nresult_sha256\n']
    document["cells"] = rows
    source.write_text(json.dumps(document))
    environment = {
        **os.environ,
        "ATLAS_REPOSITORY": str(ROOT),
        "JUPYTER_DATA_DIR": str(parent / "data"),
        "JUPYTER_CONFIG_DIR": str(parent / "config"),
        "JUPYTER_RUNTIME_DIR": str(parent / "runtime"),
        "JUPYTER_PATH": str(parent / "share/jupyter"),
        "IPYTHONDIR": str(parent / "ipython"),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "--kernel_name=atlas-admission",
            "--timeout=60",
            "--startup_timeout=20",
            "--output=native-output-kinds-executed",
            str(source),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    executed = parent / "native-output-kinds-executed.ipynb"
    completed = object_fields(json.loads(executed.read_bytes()))
    outputs = [
        output
        for cell in object_rows(completed["cells"])
        if cell["cell_type"] == "code"
        for output in object_rows(cell["outputs"])
    ]
    assert any(output["output_type"] == "execute_result" for output in outputs)
    assert any(
        output["output_type"] == "stream" and output["name"] == "stderr" for output in outputs
    )
    report = verify(source.read_bytes(), executed.read_bytes())
    stdout = report["execution_stdout"]
    assert isinstance(stdout, str)
    assert "Repeated restoration agrees: True" in stdout
    assert "native kernel stderr" not in stdout
    assert report["executed_code_cells"] == 5


@pytest.mark.parametrize("damage", ["language", "skip", "empty", "no-code", "syntax", "schema"])
def test_changed_complete_notebook_refuses(damage: str) -> None:
    """Reject actual source/metadata mutations on the complete original notebook.

    Parameters
    ----------
    damage : str
        Original format, language, skipping, empty-cell or Python syntax mutation.
    """
    document = object_fields(json.loads(NOTEBOOK.read_bytes()))
    original_cells = object_rows(document["cells"])
    code = next(cell for cell in original_cells if cell["cell_type"] == "code")
    if damage == "language":
        metadata = object_fields(document["metadata"])
        kernel = object_fields(metadata["kernelspec"])
        kernel["language"] = "javascript"
        metadata["kernelspec"] = kernel
        document["metadata"] = metadata
    elif damage == "skip":
        code["metadata"] = {"tags": ["skip-execution"]}
    elif damage == "empty":
        code["source"] = ""
    elif damage == "no-code":
        original_cells = [cell for cell in original_cells if cell["cell_type"] != "code"]
    elif damage == "syntax":
        code["source"] = "%time forbidden_magic()"
    else:
        document["nbformat"] = 3
    document["cells"] = original_cells
    with pytest.raises((ValueError, SyntaxError, ValidationError)):
        cells(json.dumps(document).encode())


def test_unexecuted_changed_and_genuinely_failed_kernel_receipts_refuse(
    kernel_receipts: tuple[Path, Path, Path, Path],
) -> None:
    """Refuse missing execution, changed original source and actual retained native errors.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Original and failed actual kernel receipts; no fabricated successful kernel output.
    """
    source, executed, failed, failed_executed = kernel_receipts
    with pytest.raises(ValueError, match="did not execute every"):
        verify(source.read_bytes(), source.read_bytes())
    with pytest.raises(ValueError, match="changed cell sources"):
        verify(failed.read_bytes(), executed.read_bytes())
    with pytest.raises(ValueError, match="returned an error"):
        verify(failed.read_bytes(), failed_executed.read_bytes())


def test_real_notebook_module_entry_point(
    kernel_receipts: tuple[Path, Path, Path, Path],
) -> None:
    """Run the exact original admission source as a real public Python module.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Genuine native original/executed notebook files passed to the module CLI.
    """
    source, executed, _, _ = kernel_receipts
    result = subprocess.run(
        [sys.executable, "-m", "tools.notebooks", str(source), "--executed", str(executed)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert object_fields(json.loads(result.stdout))["executed_code_cells"] == 5


def test_code_cell_cannot_be_hidden_as_markdown_in_a_real_kernel_receipt(
    kernel_receipts: tuple[Path, Path, Path, Path], tmp_path: Path
) -> None:
    """Refuse a changed cell role while retaining its exact genuine kernel source text.

    Parameters
    ----------
    kernel_receipts : tuple of pathlib.Path
        Complete original and executed notebooks produced by the actual Jupyter CLI.
    tmp_path : pathlib.Path
        Owning directory for a schema-valid damaged copy of the real execution result.
    """
    source, executed, _, _ = kernel_receipts
    original = executed.read_bytes()
    document = object_fields(json.loads(original))
    rows = object_rows(document["cells"])
    code = next(cell for cell in rows if cell["cell_type"] == "code")
    code["cell_type"] = "markdown"
    del code["execution_count"], code["outputs"]
    document["cells"] = rows
    damaged = tmp_path / "hidden-code-cell.ipynb"
    damaged.write_text(json.dumps(document))
    assert [cell["source"] for cell in cells(damaged.read_bytes())] == [
        cell["source"] for cell in cells(source.read_bytes())
    ]
    result = subprocess.run(
        [sys.executable, "-m", "tools.notebooks", str(source), "--executed", str(damaged)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "changed cell sources or types" in result.stderr
    assert executed.read_bytes() == original


def test_actual_changed_distribution_metadata_refuses(tmp_path: Path) -> None:
    """Refuse changed native metadata in an owned copy through the real module process.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owner-selected working-disk candidate for copied installed distribution metadata.
    """
    native = distribution("mypy")
    files = native.files
    assert files is not None
    metadata = next(path for path in files if path.name == "METADATA")
    original = Path(str(native.locate_file(metadata.parent)))
    candidate = tmp_path / original.name
    shutil.copytree(original, candidate)
    path = candidate / "METADATA"
    text = path.read_text()
    assert "Version: 2.3.1" in text
    path.write_text(text.replace("Version: 2.3.1", "Version: 0.0.0"))
    result = subprocess.run(
        [sys.executable, "-m", "tools.notebooks", str(NOTEBOOK)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Notebook native tool version mismatch: mypy" in result.stderr
