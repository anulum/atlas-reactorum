// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — first-source refusal for unqualified languages and compiled artifacts.
"use strict";
const path = require("node:path");
const { sourceFiles } = require("./source-files.cjs");
const UNQUALIFIED = new Set([
  ".ts",
  ".tsx",
  ".mts",
  ".cts",
  ".jsx",
  ".rs",
  ".go",
  ".c",
  ".h",
  ".cc",
  ".cpp",
  ".cxx",
  ".hpp",
  ".hxx",
  ".java",
  ".kt",
  ".kts",
  ".scala",
  ".cs",
  ".fs",
  ".fsx",
  ".vb",
  ".swift",
  ".m",
  ".mm",
  ".jl",
  ".mojo",
  ".zig",
  ".v",
  ".sv",
  ".vhd",
  ".vhdl",
  ".lean",
  ".proto",
  ".pyx",
  ".pxd",
  ".cu",
  ".cuh",
  ".cl",
  ".f",
  ".f90",
  ".f95",
  ".r",
  ".lua",
  ".rb",
  ".pl",
  ".hs",
  ".ex",
  ".exs",
  ".erl",
  ".bash",
  ".zsh",
  ".ps1",
  ".so",
  ".dylib",
  ".dll",
  ".pyd",
  ".node",
  ".wasm",
  ".a",
  ".o",
  ".lib",
  ".class",
  ".jar",
]);
const SUPPORTED = new Set([
  ".py",
  ".pyi",
  ".js",
  ".cjs",
  ".mjs",
  ".sh",
  ".html",
  ".css",
  ".ipynb",
]);
const ASSETS = new Set([
  ".cff",
  ".csv",
  ".frames",
  ".geojson",
  ".in",
  ".jpg",
  ".json",
  ".license",
  ".md",
  ".png",
  ".sha256",
  ".toml",
  ".tsv",
  ".txt",
  ".xlsx",
  ".yaml",
  ".yml",
  ".zip",
]);
const NAMED_FILES = new Set([
  ".editorconfig",
  ".gitattributes",
  ".gitignore",
  ".nojekyll",
  ".npmrc",
  ".prettierignore",
  "CODEOWNERS",
  "LICENSE",
  "Makefile",
  "SHA256SUMS",
]);
/**
 * Refuse source/backend formats whose complete native role has not been enrolled.
 * @returns {void} Current maintained source and assets retain their owning gate routing.
 * @throws {Error} For unknown/unqualified formats or source suffixes hidden by case differences.
 */
function main() {
  if (process.version !== "v24.21.0")
    throw Error("source-language gate requires Node v24.21.0");
  for (const file of sourceFiles([])) {
    if (file.endsWith(".d.ts")) continue;
    const suffix = path.extname(file).toLowerCase();
    if (UNQUALIFIED.has(suffix))
      throw Error(
        "source requires complete native language/backend qualification: " +
          file,
      );
    if (SUPPORTED.has(suffix) && !file.endsWith(suffix))
      throw Error(
        "source suffix must use its native gate's lowercase form: " + file,
      );
    if (
      !SUPPORTED.has(suffix) &&
      !ASSETS.has(suffix) &&
      !NAMED_FILES.has(path.basename(file))
    )
      throw Error(
        "source format requires explicit owning qualification: " + file,
      );
  }
}
if (require.main === module) main();
