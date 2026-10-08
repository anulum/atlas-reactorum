// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — complete source and native Jupyter command orchestration.
"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  os = require("node:os"),
  cp = require("node:child_process");
const { sourceFiles } = require("./source-files.cjs");
/**
 * Run one actual interpreter/module command without a shell and preserve failure.
 * @param {string} python Explicit qualified interpreter selected by the owning environment.
 * @param {string[]} args Fixed native module and complete source arguments.
 * @param {Record<string,string|undefined>} env Owned kernel, cache and temporary-directory environment.
 * @returns {void} The native process returned success within its finite deadline.
 * @throws {Error} For launch failure, timeout, signal or actual nonzero status.
 */
function run(python, args, env) {
  const result = cp.spawnSync(python, args, {
    env,
    stdio: "inherit",
    timeout: 150000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0)
    throw Error(
      "native notebook command refused: " +
        args.join(" ") +
        " status=" +
        result.status,
    );
}
/**
 * Check all original/new notebooks with locked native tools and optionally a real kernel.
 * @param {string|undefined} mode Complete static source or actual kernel execution.
 * @param {string} [workspace] Existing caller-owned temporary parent outside source.
 * @returns {void} Every source/current result qualified without changing accepted inputs.
 * @throws {Error} For absent source, unsupported mode/runtime or any native refusal.
 */
function main(mode, workspace = os.tmpdir()) {
  if (process.version !== "v24.21.0")
    throw Error("notebook gates require Node v24.21.0");
  if (!["static", "execute"].includes(mode || ""))
    throw Error("usage: node tools/notebooks.cjs static|execute [workspace]");
  const sources = sourceFiles(["*.ipynb"]);
  if (!sources.length) throw Error("no notebook source");
  const root = process.cwd(),
    python = process.env.ATLAS_PYTHON || path.resolve(".venv/bin/python");
  for (const source of sources) {
    const original = fs.readFileSync(source);
    const parent = fs.mkdtempSync(path.join(workspace, "atlas-notebook-"));
    try {
      const copied = path.join(parent, path.basename(source));
      fs.writeFileSync(copied, original, { flag: "wx" });
      const runtime = path.join(parent, "runtime");
      fs.mkdirSync(runtime);
      const env = {
        ...process.env,
        ATLAS_REPOSITORY: root,
        JUPYTER_DATA_DIR: path.join(parent, "data"),
        JUPYTER_CONFIG_DIR: path.join(parent, "config"),
        JUPYTER_RUNTIME_DIR: runtime,
        IPYTHONDIR: path.join(parent, "ipython"),
        MYPYPATH: root,
        JUPYTER_PATH: path.join(parent, "share/jupyter"),
      };
      run(python, ["-m", "tools.notebooks", copied], env);
      const config = path.join(root, "pyproject.toml");
      run(python, ["-m", "ruff", "check", "--config", config, copied], env);
      run(
        python,
        ["-m", "ruff", "format", "--check", "--config", config, copied],
        env,
      );
      run(
        python,
        ["-m", "nbqa", "mypy", copied, "--strict", "--config-file", config],
        env,
      );
      if (mode === "execute") {
        run(
          python,
          [
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            parent,
            "--name",
            "atlas-owned",
          ],
          env,
        );
        run(
          python,
          [
            "-m",
            "jupyter",
            "execute",
            "--kernel_name=atlas-owned",
            "--timeout=60",
            "--startup_timeout=20",
            "--output=executed",
            copied,
          ],
          env,
        );
        run(
          python,
          [
            "-m",
            "tools.notebooks",
            copied,
            "--executed",
            path.join(parent, "executed.ipynb"),
          ],
          env,
        );
      }
      if (
        !fs.readFileSync(copied).equals(original) ||
        !fs.readFileSync(source).equals(original)
      )
        throw Error("notebook check changed original source");
    } finally {
      fs.rmSync(parent, { recursive: true });
    }
  }
}
if (require.main === module) main(process.argv[2], process.argv[3]);
