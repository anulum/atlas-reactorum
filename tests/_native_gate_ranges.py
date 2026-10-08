# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — durable source bindings for actual native gate commands.
"""Preserve exact native gate inputs and real process evidence before candidate cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path


def run_gate(
    root: Path,
    command: Sequence[str],
    modules: Sequence[str],
    environment: Mapping[str, str],
    timeout: float,
    control: Callable[[subprocess.Popen[str]], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a real public gate with frozen source copies and its own native coverage directory.

    Parameters
    ----------
    root : pathlib.Path
        Actual candidate/index root, resolved before recording native source URLs.
    command : sequence of str
        Actual native CLI or Make command; no checker is replaced.
    modules : sequence of str
        Complete gate modules and dependencies relative to the candidate root.
    environment : mapping of str to str
        Caller-selected native tools and owned cache/kernel/workspace environment.
    timeout : float
        Finite deadline in seconds for the real public process.
    control : callable or None
        Optional real filesystem/process interaction after native exec; no checker result is replaced.

    Returns
    -------
    subprocess.CompletedProcess of str
        Original native process status and unmodified stdout/stderr.

    Raises
    ------
    AssertionError
        A complete recorded gate source changes during the real command.
    subprocess.TimeoutExpired
        The native command does not finish within its owning deadline.
    """
    root = root.resolve(strict=True)
    before = {name: (root / name).read_bytes() for name in modules}
    parent = Path(environment.get("ATLAS_TEST_WORKSPACE", tempfile.gettempdir()))
    receipt = Path(tempfile.mkdtemp(prefix="gate-native-ranges-", dir=parent))
    bindings = []
    for name, content in before.items():
        target = receipt / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        bindings.append(
            {
                "url": (root / name).as_uri(),
                "source_sha256": hashlib.sha256(content).hexdigest(),
                "preserved_source": str(target),
            }
        )
    process = subprocess.Popen(
        list(command),
        cwd=root,
        env={**environment, "NODE_V8_COVERAGE": str(receipt)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        if control is not None:
            control(process)
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    result = subprocess.CompletedProcess(list(command), process.returncode, stdout, stderr)
    assert {name: (root / name).read_bytes() for name in before} == before
    (receipt / "stdout").write_text(result.stdout)
    (receipt / "stderr").write_text(result.stderr)
    (receipt / "binding.json").write_text(
        json.dumps(
            {
                "sources": bindings,
                "input_source_unchanged": True,
                "command": list(command),
                "status": result.returncode,
            }
        )
    )
    return result


def run_node_fault(
    root: Path, gate: str, modules: Sequence[str], environment: Mapping[str, str], fault: str
) -> subprocess.CompletedProcess[str]:
    """Exercise real missing-runtime and terminated-child faults with original native tool metadata.

    Parameters
    ----------
    root : pathlib.Path
        Actual isolated source/index and hard-linked installed native graph.
    gate : str
        Complete public gate script relative to the candidate root.
    modules : sequence of str
        Owning full gate sources whose byte identity is preserved by the native collector.
    environment : mapping of str to str
        Actual locked native environment and owned working-disk cache/workspace.
    fault : str
        Missing child runtime path or real child termination after native exec.

    Returns
    -------
    subprocess.CompletedProcess of str
        Actual public gate failure, with original metadata bytes and real native process evidence.
    """
    root = root.resolve(strict=True)
    node = shutil.which("node")
    assert node is not None
    executable = root / "native-node"
    shutil.copy2(node, executable)
    metadata = root / "node_modules/prettier/package.json"
    original = metadata.read_bytes()
    metadata.unlink()
    os.mkfifo(metadata)
    with os.fdopen(os.open(metadata, os.O_RDWR), "wb", buffering=0) as pipe:

        def control(process: subprocess.Popen[str]) -> None:
            """Synchronize real metadata delivery with the native parent's actual file/process handles."""
            deadline = time.monotonic() + 30
            descriptors = Path("/proc") / str(process.pid) / "fd"
            while time.monotonic() < deadline:
                handles = list(descriptors.iterdir())
                opened = False
                for handle in handles:
                    with suppress(FileNotFoundError):
                        if handle.readlink() == metadata:
                            opened = True
                            break
                if opened:
                    break
                time.sleep(0.005)
            else:
                raise AssertionError("native parent did not open original metadata")
            if fault == "missing-runtime":
                executable.rename(root / "native-node-retained")
            pipe.write(original)
            pipe.close()
            if fault == "terminated-child":
                children = Path("/proc") / str(process.pid) / "task" / str(process.pid) / "children"
                while time.monotonic() < deadline:
                    values = children.read_text().split()
                    if values:
                        os.kill(int(values[0]), signal.SIGTERM)
                        break
                    time.sleep(0.005)
                else:
                    raise AssertionError("native child was not created")

        return run_gate(root, [str(executable), gate, "format"], modules, environment, 60, control)
