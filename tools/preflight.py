#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tools/preflight.py

"""Repository-wide checks that the per-module gates cannot express.

Each check fails closed. A check that cannot execute reports failure rather
than success, because a check that never ran has told you nothing — the
failure mode that produced a false green in this repository once already.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urlsplit

# The native file entry point also resolves the repository namespace when
# invoked from another working directory; importing the module needs no install.
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.rebuild import repository_files, reproduce

ROOT = Path(__file__).resolve().parents[1]

# Content shaped like a credential. The vault is the only place such values
# may exist, and it is not part of this repository.
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][^'\"]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\baws_secret_access_key\b\s*[:=]"),
)
HEADER = (
    "SPDX-" + "License-Identifier: AGPL-3.0-or-later",
    "Commercial license available",
    "© Concepts 1996–2026 Miroslav Šotek. All rights reserved.",
    "© Code 2020–2026 Miroslav Šotek. All rights reserved.",
    "ORCID: 0009-0009-3560-0851",
    "Contact: www.anulum.li | protoscience@anulum.li",
)


def check_reproducibility(
    root: Path = ROOT, workspace: Path | None = None, *, timeout: float = 1800
) -> list[str]:
    """Rebuild every offline release product in an isolated source tree.

    Parameters
    ----------
    root : pathlib.Path
        Accepted source and release products.
    workspace : pathlib.Path or None
        Existing external parent for a new temporary source tree.
    timeout : float
        Per-builder timeout in seconds.

    Returns
    -------
    list of str
        Failures from the real taxonomy, integration, coverage and inventory
        pipeline, without changing accepted files.
    """
    return reproduce(root, workspace, timeout=timeout)


def check_docs(root: Path = ROOT) -> list[str]:
    """Verify every repository-relative path cited in the docs exists.

    Parameters
    ----------
    root : pathlib.Path
        Candidate containing public Markdown and its cited files.

    Returns
    -------
    list of str
        Failures, empty when every cited path resolves.
    """
    failures: list[str] = []
    root = root.resolve(strict=True)
    link = re.compile(r"\]\(([^)\n]+)\)")
    for doc in repository_files(root):
        if doc.suffix.lower() != ".md":
            continue
        for target in link.findall(doc.read_text(encoding="utf-8")):
            target = target.partition(' "')[0].strip().removeprefix("<").removesuffix(">")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (doc.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                failures.append(f"docs: {doc.relative_to(root)} cites a missing candidate path")
    return failures


def check_secrets(root: Path = ROOT) -> list[str]:
    """Refuse any credential-shaped content outside the vault.

    Parameters
    ----------
    root : pathlib.Path
        Candidate to scan; binary files and private trees are not text inputs.

    Returns
    -------
    list of str
        Failures, empty when nothing credential-shaped is present.
    """
    failures: list[str] = []
    for path in repository_files(root):
        if path.suffix in {".png", ".jpg", ".pdf", ".zip", ".ndjson"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            if path.suffix in {".py", ".sh", ".cjs", ".md"}:
                failures.append(f"secrets: {path.relative_to(root)} is not UTF-8 text")
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secrets: {path.relative_to(root)} matches {pattern.pattern[:40]}")
                break
    return failures


def check_headers(root: Path = ROOT) -> list[str]:
    """Require the branding header on every source file.

    Parameters
    ----------
    root : pathlib.Path
        Candidate containing Python, shell and CommonJS source scripts.

    Returns
    -------
    list of str
        Failures, empty when every source carries the header.
    """
    failures: list[str] = []
    for path in repository_files(root):
        if path.suffix not in {".py", ".sh", ".cjs"}:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("#!"):
            lines = lines[1:]
        prefix = "// " if path.suffix == ".cjs" else "# "
        if (
            lines[:6] != [prefix + line for line in HEADER]
            or len(lines) < 7
            or not lines[6].startswith(prefix + "Atlas Reactorum — ")
        ):
            failures.append(f"headers: {path.relative_to(root)} lacks the seven-line header")
    return failures


CHECKS: dict[str, Callable[[Path], list[str]]] = {
    "reproducibility": check_reproducibility,
    "docs": check_docs,
    "secrets": check_secrets,
    "headers": check_headers,
}


def main(argv: list[str] | None = None) -> int:
    """Run the requested checks and report.

    Parameters
    ----------
    argv : list of str or None
        Command-line arguments.

    Returns
    -------
    int
        Zero when every requested check passed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", choices=sorted(CHECKS), action="append")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--timeout", type=float, default=1800)
    arguments = parser.parse_args(argv)
    selected = arguments.check or sorted(CHECKS)

    failures: list[str] = []
    for name in selected:
        try:
            if name == "reproducibility":
                found = check_reproducibility(
                    arguments.root, arguments.workspace, timeout=arguments.timeout
                )
            else:
                found = CHECKS[name](arguments.root)
        except (OSError, UnicodeError, ValueError):
            found = [f"{name}: candidate files cannot be read"]
        status = "FAIL" if found else "ok"
        print(f"{name:16s} {status}")
        failures.extend(found)

    for failure in failures:
        print(f"  - {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
