// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — owning native source discovery, including new roots.
"use strict";
const fs = require("node:fs"),
  childProcess = require("node:child_process");
/**
 * Discover tracked and new unignored source, refusing unavailable files and links.
 * @param {string[]} patterns Git source pathspecs, applied to the complete checkout.
 * @returns {string[]} Unique relative paths from actual Git discovery.
 * @throws {Error} When Git fails or a discovered source cannot be read as a regular file.
 */
function sourceFiles(patterns) {
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
      ...patterns,
    ],
    { encoding: "utf8" },
  );
  const files = output.split("\0").filter(Boolean);
  for (const file of files) {
    const info = fs.lstatSync(file);
    if (!info.isFile() || info.isSymbolicLink())
      throw Error("native source unavailable or symlink: " + file);
    fs.accessSync(file, fs.constants.R_OK);
  }
  return files;
}
module.exports = { sourceFiles };
