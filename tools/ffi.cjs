// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native FFI imports bound to complete qualified source.
"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  crypto = require("node:crypto"),
  cp = require("node:child_process");
const { sourceFiles } = require("./source-files.cjs");
const LIBC_OBSERVER = "tests/test_facility_fields_build.py";
const LIBC_SOURCE =
  "c6b793577c631a04625e37d7666c7542273770fd1b8083d2a5381c7639a4edc9";
/**
 * Bind authorized native source and require zero native FFI findings elsewhere.
 * The libc inotify observer's complete source is pinned; another file or any byte change needs fresh qualification.
 * @returns {void} All direct Python FFI imports belong to the current complete native observer.
 * @throws {Error} For missing tools, any native finding or a new/changed unqualified interface.
 */
function main() {
  if (process.version !== "v24.21.0")
    throw Error("FFI gate requires Node v24.21.0");
  const files = sourceFiles(["*.py", "*.pyi", "*.ipynb"]);
  if (!files.length) throw Error("no Python FFI source");
  const python = process.env.ATLAS_PYTHON || path.resolve(".venv/bin/python");
  const version = cp.execFileSync(python, ["-m", "ruff", "--version"], {
    encoding: "utf8",
    timeout: 30000,
  });
  if (version.trim() !== "ruff 0.16.9")
    throw Error("native FFI checker version mismatch");
  for (const file of files) {
    if (
      file === LIBC_OBSERVER &&
      crypto
        .createHash("sha256")
        .update(fs.readFileSync(file))
        .digest("hex") !== LIBC_SOURCE
    )
      throw Error("FFI source needs complete native qualification: " + file);
  }
  const unqualified = files.filter((file) => file !== LIBC_OBSERVER);
  if (!unqualified.length) return;
  const policy =
    'lint.flake8-tidy-imports.banned-api = {ctypes = {msg = "Native FFI needs complete owning qualification"}, cffi = {msg = "Native FFI needs complete owning qualification"}}';
  cp.execFileSync(
    python,
    [
      "-m",
      "ruff",
      "check",
      "--isolated",
      "--ignore-noqa",
      "--select",
      "TID251",
      "--config",
      policy,
      "--",
      ...unqualified,
    ],
    { stdio: "inherit", timeout: 120000 },
  );
}
if (require.main === module) main();
