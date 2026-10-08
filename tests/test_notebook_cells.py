# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete original notebook cells through genuine Jupyter kernels.
"""Exercise accepted research output and native cell refusals with exact original source bindings."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import coverage

from tools.notebooks import cell_source, cells, verify
from tools.rebuild import repository_files
from tools.research_objects import object_fields, object_rows

from ._native_gate_ranges import run_gate

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = Path("examples/research/comparison.ipynb")
CASES = (
    "accepted",
    "missing-profile",
    "manifest-array",
    "profile_sha256",
    "bundle_sha256",
    "comparison_file",
    "changed-consumer-state",
)


def prepare_case(root: Path, source: Path, original: bytes, case: str) -> None:
    """Damage actual candidate inputs or insert one explicit consumer-state countercell.

    Parameters
    ----------
    root : pathlib.Path
        Complete independent copy of the original repository.
    source : pathlib.Path
        Kernel input copied from the original notebook.
    original : bytes
        Exact maintained notebook before execution or deliberate controls.
    case : str
        Accepted snapshot, absent profile, malformed manifest field or changed consumer state.
    """
    manifest_file = root / "examples/research/comparison-manifest.json"
    if case == "missing-profile":
        (root / "metadata/evidence_profiles/profiles.json").unlink()
    elif case == "manifest-array":
        manifest_file.write_text("[]\n")
    elif case in {"profile_sha256", "bundle_sha256", "comparison_file"}:
        manifest = object_fields(json.loads(manifest_file.read_text()))
        manifest[case] = None
        manifest_file.write_text(json.dumps(manifest))
    elif case == "changed-consumer-state":
        document = object_fields(json.loads(original))
        ordered = object_rows(document["cells"])
        last = max(i for i, cell in enumerate(ordered) if cell["cell_type"] == "code")
        ordered.insert(
            last,
            {
                "cell_type": "code",
                "id": "deliberate-consumer-state",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": 'comparison["metadata_license"] = "deliberately changed consumer state"',
            },
        )
        document["cells"] = ordered
        source.write_text(json.dumps(document))


def execute_case(root: Path, work: Path, source: Path) -> tuple[coverage.Coverage, str, int]:
    """Run the real native install and execution commands with owned startup and durable receipts.

    Parameters
    ----------
    root : pathlib.Path
        Complete actual candidate source and products.
    work : pathlib.Path
        Retained working-disk kernel, source and coverage directory.
    source : pathlib.Path
        Exact kernel input; deliberate controls retain all five original code cells.

    Returns
    -------
    tuple of coverage.Coverage, str and int
        Loaded native arcs, actual execution stderr and native terminal status.
    """
    profile = work / "ipython/profile_default/startup"
    profile.mkdir(parents=True)
    shutil.copy2(root / "tests/_notebook_kernel_coverage.py", profile / "00_coverage.py")
    (work / "kernel-temp").mkdir()
    (work / "runtime").mkdir()
    environment = {
        **os.environ,
        "ATLAS_REPOSITORY": str(root),
        "ATLAS_CELL_COVERAGE": str(work / "coverage"),
        "ATLAS_CELL_BINDINGS": str(work / "bindings.json"),
        "TMPDIR": str(work / "kernel-temp"),
        "JUPYTER_DATA_DIR": str(work / "data"),
        "JUPYTER_CONFIG_DIR": str(work / "config"),
        "JUPYTER_RUNTIME_DIR": str(work / "runtime"),
        "JUPYTER_PATH": str(work / "share/jupyter"),
        "IPYTHONDIR": str(work / "ipython"),
        "NODE_PATH": str(ROOT / "node_modules"),
    }
    modules = ["tests/_notebook_kernel_coverage.py", "tools/research_comparison.py"]
    installed = run_gate(
        root,
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            str(work),
            "--name",
            "atlas-cell-controls",
        ],
        modules,
        environment,
        120,
    )
    assert installed.returncode == 0, installed.stderr
    executed = run_gate(
        root,
        [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "--kernel_name=atlas-cell-controls",
            "--timeout=60",
            "--startup_timeout=20",
            "--output=executed",
            str(source),
        ],
        modules,
        environment,
        120,
    )
    cov = coverage.Coverage(data_file=str(work / "coverage"), config_file=False)
    cov.load()
    return cov, executed.stderr, executed.returncode


def test_all_original_cells_and_native_decision_paths() -> None:
    """Require all original statements and real kernel refusal/acceptance arcs without inventing AST exits.

    Notes
    -----
    IPython compiles top-level statements separately. Its genuine frame-exit
    arcs differ from coverage.py's whole-module AST successors. Both native
    outcomes of every original decision are required explicitly; no arc is
    added, replaced or excluded to turn the AST branch report green.
    """
    parent = Path(
        tempfile.mkdtemp(
            prefix="notebook-cell-controls-",
            dir=os.environ.get("ATLAS_TEST_WORKSPACE", tempfile.gettempdir()),
        )
    )
    original = (ROOT / NOTEBOOK).read_bytes()
    texts = [cell_source(cell) for cell in cells(original) if cell["cell_type"] == "code"]
    observed: dict[int, set[int]] = {i: set() for i in range(len(texts))}
    arcs: dict[int, set[tuple[int, int]]] = {i: set() for i in range(len(texts))}
    statements: dict[int, set[int]] = {}
    ast_statements: dict[int, set[int]] = {}
    receipts = []
    for case in CASES:
        work = parent / case
        root = work / "candidate"
        root.mkdir(parents=True)
        for item in repository_files(ROOT):
            target = root / item.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
        source = work / "comparison.ipynb"
        source.write_bytes(original)
        prepare_case(root, source, original, case)
        before = source.read_bytes()
        actual_texts = [cell_source(cell) for cell in cells(before) if cell["cell_type"] == "code"]
        assert [text for text in actual_texts if text in texts] == texts
        cov, stderr, status = execute_case(root, work, source)
        assert source.read_bytes() == before
        assert (root / NOTEBOOK).read_bytes() == original
        if case == "accepted":
            assert status == 0, stderr
            result = verify(before, (work / "executed.ipynb").read_bytes())
            assert result["executed_code_cells"] == 5
            assert "a049f8101295e041f2db9a1836273decf5507c98072add1043f0dd0882728406" in str(
                result["execution_stdout"]
            )
        else:
            assert status != 0 and "ValueError" in stderr, stderr
            expected = {
                "missing-profile": "Set ATLAS_REPOSITORY",
                "manifest-array": "retained manifest must be an object",
                "changed-consumer-state": "repeated comparison did not reproduce",
            }.get(case, "retained manifest needs string digests")
            assert expected in stderr, stderr
        bindings = object_rows(json.loads((work / "bindings.json").read_text()))
        for binding in bindings:
            native_text = binding["text"]
            filename = binding["filename"]
            assert isinstance(native_text, str) and isinstance(filename, str)
            assert hashlib.sha256(native_text.encode()).hexdigest() == binding["sha256"]
            assert Path(filename).read_text() == native_text
            assert filename in cov.get_data().measured_files()
            matching = [i for i, text in enumerate(texts) if native_text == text + "\n"]
            if not matching:
                assert case == "changed-consumer-state" and native_text == actual_texts[-2] + "\n"
                continue
            assert len(matching) == 1
            index = matching[0]
            ast_statements[index] = set(cov.analysis2(filename)[1])
            native_frames = object_rows(binding["entered_native_frames"])
            assert native_frames
            native_lines = set()
            for frame in native_frames:
                for instruction in object_rows(frame["instructions"]):
                    line = instruction["line"]
                    if isinstance(line, int) and line > 0:
                        native_lines.add(line)
            statements.setdefault(index, set()).update(native_lines)
            observed[index].update(cov.get_data().lines(filename) or [])
            arcs[index].update(cov.get_data().arcs(filename) or [])
        cov.json_report(outfile=str(work / "native-ast-report.json"))
        receipts.append({"case": case, "status": status, "work": str(work)})
    missing = {str(i): sorted(statements[i] - observed[i]) for i in range(len(texts))}
    required = {
        0: {
            (10, 11),
            (10, -1),
            (16, 17),
            (16, -1),
            (22, 23),
            (22, 26),
            (23, 24),
            (23, 26),
            (24, -1),
            (24, 26),
        },
        4: {(2, 3), (2, -1)},
    }
    absent_arcs = {str(i): sorted(expected - arcs[i]) for i, expected in required.items()}
    (parent / "summary.json").write_text(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(original).hexdigest(),
                "cases": receipts,
                "missing_statements": missing,
                "missing_ast_statements": {
                    str(i): sorted(ast_statements[i] - observed[i]) for i in range(len(texts))
                },
                "statement_scope": "lines from actual entered native compiled frames",
                "missing_native_decision_arcs": absent_arcs,
                "native_arcs": {str(i): sorted(value) for i, value in arcs.items()},
                "ast_branch_report_is_distinct": True,
            },
            indent=2,
        )
    )
    assert len(statements) == 5 and not any(missing.values()), missing
    assert not any(absent_arcs.values()), absent_arcs
    assert (ROOT / NOTEBOOK).read_bytes() == original
