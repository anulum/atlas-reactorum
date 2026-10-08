// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native generated Python declarations and actual runtime binding.
"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  os = require("node:os"),
  cp = require("node:child_process");
const { sourceFiles } = require("./source-files.cjs");
/**
 * Run a real locked Python source/interface tool and retain failure propagation.
 * @param {string} python Selected qualified interpreter.
 * @param {string[]} args Fixed native tool and source arguments.
 * @param {Record<string,string|undefined>} env Owning temporary/cache/import environment.
 * @returns {void} Actual native process succeeded within its deadline.
 * @throws {Error} For missing tool, native findings, timeout or signal.
 */
function run(python, args, env) {
  const result = cp.spawnSync(python, args, {
    env,
    stdio: "inherit",
    timeout: 120000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0)
    throw Error("native Python stub check failed: " + args.join(" "));
}
/**
 * Bind every tracked/new stub to the actual native source interface and runtime.
 * @param {string} [workspace] Existing owner-selected temporary parent.
 * @returns {void} All applicable interfaces match; absence of Python stubs is explicit.
 * @throws {Error} For absent implementation, changed declaration bytes or runtime mismatch.
 */
function main(workspace = os.tmpdir()) {
  if (process.version !== "v24.21.0")
    throw Error("Python stub gate requires Node v24.21.0");
  const stubs = sourceFiles(["*.pyi"]),
    root = process.cwd(),
    python = process.env.ATLAS_PYTHON || path.resolve(".venv/bin/python");
  for (const stub of stubs) {
    const source = stub.slice(0, -1);
    if (!sourceFiles([source]).includes(source))
      throw Error(
        "Python stub needs its qualified source counterpart: " + stub,
      );
    const original = fs.readFileSync(stub),
      implementation = fs.readFileSync(source);
    const parent = fs.mkdtempSync(path.join(workspace, "atlas-stub-"));
    try {
      const env = {
        ...process.env,
        MYPYPATH: path.resolve(path.dirname(stub)),
        PYTHONPATH: path.resolve(path.dirname(source)),
      };
      run(
        python,
        [
          "-c",
          "from importlib.metadata import version\nif version('mypy') != '2.3.1' or version('ruff') != '0.16.9':\n    raise RuntimeError('native Python stub tool version mismatch')",
        ],
        env,
      );
      run(
        python,
        [
          "-c",
          "from mypy.stubgen import main; main()",
          "--no-import",
          "--parse-only",
          "--include-private",
          "-o",
          parent,
          source,
        ],
        env,
      );
      const generated = path.join(parent, path.basename(stub));
      run(python, ["-m", "ruff", "format", generated], env);
      const lines = implementation.toString("utf8").split("\n");
      if (lines[0].startsWith("#!")) lines.shift();
      const expected =
        lines.slice(0, 7).join("\n") +
        "\n" +
        fs.readFileSync(generated, "utf8");
      if (original.toString("utf8") !== expected)
        throw Error(
          "Python stub differs from native source interface: " + stub,
        );
      run(
        python,
        [
          "-m",
          "mypy.stubtest",
          "--mypy-config-file",
          path.join(root, "pyproject.toml"),
          "--strict-type-check-only",
          path.basename(source, ".py"),
        ],
        env,
      );
      if (
        !fs.readFileSync(stub).equals(original) ||
        !fs.readFileSync(source).equals(implementation)
      )
        throw Error("stub qualification changed input source");
    } finally {
      fs.rmSync(parent, { recursive: true });
    }
  }
  console.log("Native Python stub counterparts qualified: " + stubs.length);
}
if (require.main === module) main(process.argv[2]);
