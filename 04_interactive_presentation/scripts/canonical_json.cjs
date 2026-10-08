// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original canonical JSON and native wire-shape admission.
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

/**
 * Parse only the original canonical two-space JSON representation with a newline.
 * Duplicate keys and lossy nonfinite numeric cells cannot reproduce those bytes.
 * @param {string} text Original complete JSON input, never rewritten.
 * @param {string} [refusal] Owning caller's authored canonical-format error.
 * @returns {unknown} Original parsed cells before owning semantic admission.
 * @throws {Error} JSON syntax or original canonical representation is invalid.
 */
function canonical(
  text,
  refusal = "Comparison input requires canonical two-space JSON and a final newline",
) {
  /** @type {unknown} */
  const value = JSON.parse(text);
  if (JSON.stringify(value, null, 2) + "\n" !== text) {
    throw new Error(refusal);
  }
  return value;
}

/**
 * Read exact UTF-8 JSON and optionally admit its complete owning wire shape.
 * Integrity, chronology and source/citation binding remain with native owners.
 * @param {string} file Original input file whose byte custody is retained.
 * @param {"profiles"|"history"|"proposal"} [kind] Complete owning wire contract; omitted when an independent semantic owner checks the raw fields.
 * @param {string} [refusal] Owning caller's authored canonical-format error.
 * @returns {unknown} Original parsed cells after canonical and optional wire-shape validation.
 * @throws {Error} UTF-8, canonical representation, native tool or owning schema fails.
 */
function read(
  file,
  kind,
  refusal = "History input needs canonical two-space JSON and a final newline",
) {
  const raw = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(
    fs.readFileSync(file),
  );
  const value = canonical(raw, refusal);
  if (kind !== undefined) {
    execFileSync(
      process.env.ATLAS_PYTHON || "python3",
      [path.resolve(__dirname, "../../tools/evidence_history_inputs.py"), kind],
      {
        input: raw,
        encoding: "utf8",
        timeout: 30000,
        stdio: ["pipe", "ignore", "pipe"],
      },
    );
  }
  return value;
}

module.exports = { canonical, read };
