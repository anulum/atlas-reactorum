// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — maintained HTML/CSS native source entry point.
"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  cp = require("node:child_process");
const { sourceFiles } = require("./source-files.cjs"),
  css = require("./css.cjs");
/**
 * Require the declared exact native tool version from its real installed metadata.
 * @param {string} name Native npm package name.
 * @param {string} expected Exact qualification version.
 * @returns {void} Metadata agrees; no replacement tool is downloaded.
 * @throws {Error} For missing, malformed or mismatched native packages.
 */
function version(name, expected) {
  const metadata = /** @type {unknown} */ (
    JSON.parse(
      fs.readFileSync(path.join("node_modules", name, "package.json"), "utf8"),
    )
  );
  if (
    !metadata ||
    typeof metadata !== "object" ||
    !("version" in metadata) ||
    metadata.version !== expected
  )
    throw Error("native web tool version mismatch: " + name);
}
/**
 * Execute the native CLI with its original status and a finite deadline.
 * @param {string} executable Real package-relative script.
 * @param {string[]} args Owning source/configuration arguments.
 * @returns {number} Actual native success/failure status.
 * @throws {Error} If the real tool fails to start or has no terminal status.
 */
function native(executable, args) {
  const result = cp.spawnSync(process.execPath, [executable, ...args], {
    stdio: "inherit",
    timeout: 120000,
  });
  if (result.error) throw result.error;
  if (result.status === null)
    throw Error("native web tool has no terminal status");
  return result.status;
}
/**
 * Check every maintained/new web source through its owning parser and formatter.
 * @param {string|undefined} mode HTML semantics, CSS grammar or web formatting.
 * @returns {number} Real owning native status.
 * @throws {Error} For absent source, tool, unsupported mode or native CSS failure.
 */
function main(mode) {
  if (process.version !== "v24.21.0")
    throw Error("native web gates require Node v24.21.0");
  if (!["html", "css", "format"].includes(mode || ""))
    throw Error("usage: node tools/web.cjs html|css|format");
  const files = sourceFiles(
    mode === "html"
      ? ["*.html"]
      : mode === "css"
        ? ["*.css"]
        : ["*.html", "*.css"],
  );
  if (!files.length) throw Error("no native web source");
  if (mode === "html") {
    version("html-validate", "11.16.2");
    return native("node_modules/html-validate/bin/html-validate.mjs", [
      "--config",
      "tools/htmlvalidate.cjs",
      "--max-warnings",
      "0",
      "--",
      ...files,
    ]);
  }
  if (mode === "css") {
    version("css-tree", "3.2.1");
    for (const file of files) css.validate(fs.readFileSync(file, "utf8"));
    return 0;
  }
  version("prettier", "3.9.9");
  return native("node_modules/prettier/bin/prettier.cjs", [
    "--check",
    "--",
    ...files,
  ]);
}
if (require.main === module) process.exitCode = main(process.argv[2]);
