// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native reconstruction of original comparison exports
"use strict";
const fs = require("node:fs");
const { createHash } = require("node:crypto");
const { isDeepStrictEqual } = require("node:util");
require("../taxonomy-evidence-profile.js");
require("../taxonomy-comparison.js");

function canonical(text) {
  const value = JSON.parse(text);
  if (JSON.stringify(value, null, 2) + "\n" !== text) {
    throw new Error("Comparison input requires canonical two-space JSON and a final newline");
  }
  return value;
}

/**
 * Restore an original export against an explicit complete-profile snapshot.
 * @param {object} document Complete source-validated original profile document.
 * @param {string} snapshot Expected profile digest from an independently retained manifest.
 * @param {string} text Original canonical downloaded comparison, retained without changes.
 * @param {string} digest Expected original file SHA-256 from the caller's trusted manifest.
 * @returns {Promise<object>} Exact original comparison; no numeric conversion or source edits.
 * @throws {Error} On any hash, identity, rights, claim, source or compatibility mismatch.
 */
async function restore(document, snapshot, text, digest) {
  if (!/^[a-f0-9]{64}$/.test(digest) || createHash("sha256").update(text, "utf8").digest("hex") !== digest) {
    throw new Error("Original comparison file digest does not match");
  }
  const bundle = canonical(text);
  const expected = await globalThis.AtlasTaxonomyComparison.createComparison(
    document, snapshot, bundle.selection.entry_ids,
  );
  if (!isDeepStrictEqual(bundle, expected)) {
    throw new Error("Comparison differs from the original selected profiles and sources");
  }
  return bundle;
}

/**
 * Export or restore a real comparison through the existing public model.
 * @param {string[]} args --export PROFILE_JSON SNAPSHOT ENTRY ENTRY [ENTRY], or
 * --restore PROFILE_JSON SNAPSHOT BUNDLE_JSON BUNDLE_SHA256.
 * @returns {Promise<object>} Original versioned bundle, suitable for canonical JSON output.
 * @throws {Error} On invalid arguments, unreadable inputs or any refused source binding.
 */
async function run(args) {
  const [mode, file, snapshot, ...rest] = args;
  if ((mode !== "--export" && mode !== "--restore") || rest.length < 2 || rest.length > 3 ||
      (mode === "--restore" && rest.length !== 2)) {
    throw new Error("Use --export PROFILE SNAPSHOT ENTRY ENTRY [ENTRY] or --restore PROFILE SNAPSHOT BUNDLE SHA256");
  }
  const document = canonical(new TextDecoder("utf-8", { fatal: true }).decode(fs.readFileSync(file)));
  if (mode === "--export") {
    return globalThis.AtlasTaxonomyComparison.createComparison(document, snapshot, rest);
  }
  const text = new TextDecoder("utf-8", { fatal: true }).decode(fs.readFileSync(rest[0]));
  return restore(document, snapshot, text, rest[1]);
}

module.exports = { restore, run };
if (require.main === module) {
  Promise.resolve().then(() => run(process.argv.length > 2 ? process.argv.slice(2) :
    JSON.parse(fs.readFileSync(0, "utf8")))).then(bundle => {
    process.stdout.write(JSON.stringify(bundle, null, 2) + "\n");
  }, () => {
    process.stderr.write("research comparison: input or source binding refused\n");
    process.exitCode = 2;
  });
}
