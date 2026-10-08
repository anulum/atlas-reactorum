// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native JavaScript source discovery and tool execution.

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const childProcess = require("node:child_process");

/**
 * Read one native package version without accepting unvalidated JSON values.
 * @param {string} filename Package metadata file.
 * @returns {string} Declared version.
 * @throws {Error} If metadata is absent, unreadable or malformed.
 */
function packageVersion(filename) {
  /** @type {unknown} */
  const data = JSON.parse(fs.readFileSync(filename, "utf8"));
  if (
    !data ||
    typeof data !== "object" ||
    !("version" in data) ||
    typeof data.version !== "string"
  ) {
    throw new Error("native package metadata has no version: " + filename);
  }
  return data.version;
}

/**
 * Discover every tracked and new unignored JavaScript source in this checkout.
 * @returns {string[]} Relative source paths including newly created directories.
 * @throws {Error} If Git fails or any discovered source is missing, unreadable or a symlink.
 */
function sourceFiles() {
  const output = childProcess.execFileSync(
    "git",
    [
      "ls-files",
      "--cached",
      "--others",
      "--exclude-standard",
      "--deduplicate",
      "-z",
      "--",
      "*.js",
      "*.cjs",
      "*.mjs",
      "*.d.ts",
    ],
    { encoding: "utf8" },
  );
  const files = output.split("\0").filter(Boolean);
  if (files.length === 0) throw new Error("no native JavaScript source");
  for (const file of files) {
    const info = fs.lstatSync(file);
    if (!info.isFile() || info.isSymbolicLink()) {
      throw new Error("native source unavailable or symlink: " + file);
    }
    fs.accessSync(file, fs.constants.R_OK);
  }
  return files;
}

/**
 * Run the locked native executable and retain its real exit status.
 * @param {string} packageName Package owning the native tool.
 * @param {string} version Required exact version.
 * @param {string} executable Package-relative native entry point.
 * @param {string[]} arguments_ Native arguments.
 * @returns {number} Actual native exit status.
 * @throws {Error} If the tool is absent, changed, unavailable or terminates without a status.
 */
function nativeTool(packageName, version, executable, arguments_) {
  const directory = path.resolve("node_modules", packageName);
  if (packageVersion(path.join(directory, "package.json")) !== version) {
    throw new Error("native tool version mismatch: " + packageName);
  }
  const result = childProcess.spawnSync(
    process.execPath,
    [path.join(directory, executable), ...arguments_],
    { stdio: "inherit" },
  );
  if (result.error) throw result.error;
  if (result.status === null) {
    throw new Error("native tool terminated without status: " + packageName);
  }
  return result.status;
}

/**
 * Dispatch the complete owning lint, strict-type or formatting check.
 * @param {string|undefined} mode Native check selected by the command line.
 * @returns {number} Native check status.
 * @throws {Error} If the mode, runtime, source set or locked tool is unavailable.
 */
function main(mode) {
  if (!["lint", "types", "format"].includes(mode || "")) {
    throw new Error("usage: node tools/javascript.cjs lint|types|format");
  }
  if (process.version !== "v24.21.0") {
    throw new Error("native JavaScript requires Node v24.21.0");
  }
  const files = sourceFiles();
  if (mode === "lint") {
    return nativeTool("eslint", "10.12.0", "bin/eslint.js", [
      "--max-warnings=0",
      "--config",
      "eslint.config.mjs",
      "--",
      ...files,
    ]);
  }
  if (mode === "types") {
    return nativeTool("typescript", "6.0.3", "bin/tsc", [
      "--project",
      "jsconfig.json",
    ]);
  }
  return nativeTool("prettier", "3.9.9", "bin/prettier.cjs", [
    "--check",
    "--",
    ...files,
  ]);
}

if (require.main === module) process.exitCode = main(process.argv[2]);
