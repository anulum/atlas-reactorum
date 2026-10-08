// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — validated original profile and taxonomy test inputs.
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { createHash } = require("node:crypto");
const { execFileSync } = require("node:child_process");
const {
  readCatalogue,
  completeCatalogue,
} = require("../04_interactive_presentation/scripts/taxonomy_export_inputs.cjs");
const {
  readCitations,
} = require("../04_interactive_presentation/scripts/taxonomy_citations.cjs");

/**
 * Load original inputs through their actual complete production validators.
 * The Python CLI validates every profile against schema, source hashes and
 * original claims before the checked bytes acquire a profile type. The Node
 * catalogue/citation readers separately bind the actual classic-script rows.
 * @param {string} root Canonical repository containing the unchanged inputs.
 * @returns {{document: import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument, rows: import("../04_interactive_presentation/scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]}} Whole validated profiles and original rows.
 * @throws {Error} A native validator fails, an input changes or its byte-bound document differs.
 */
function loadProfileFixture(root) {
  const filename = path.join(root, "metadata/evidence_profiles/profiles.json");
  const bytes = fs.readFileSync(filename);
  const taxonomyPath = path.join(
    root,
    "04_interactive_presentation/data/taxonomy-expanded.js",
  );
  const taxonomyBytes = fs.readFileSync(taxonomyPath);
  const snapshot = createHash("sha256").update(taxonomyBytes).digest("hex");
  const output = execFileSync(
    process.env.ATLAS_PYTHON || "python3",
    [
      path.join(root, "metadata/evidence_profiles/validate.py"),
      "--root",
      root,
      "--snapshot",
      snapshot,
    ],
    { encoding: "utf8", timeout: 30000, maxBuffer: 8 * 1024 * 1024 },
  );
  /** @type {unknown} */
  const original = JSON.parse(bytes.toString("utf8"));
  /** @type {unknown} */
  const validated = JSON.parse(output);
  assert.deepEqual(
    validated,
    original,
    "Native validator returned a different profile document",
  );
  assert.deepEqual(
    fs.readFileSync(filename),
    bytes,
    "Profile input changed during validation",
  );
  assert.deepEqual(
    fs.readFileSync(taxonomyPath),
    taxonomyBytes,
    "Taxonomy input changed during validation",
  );
  const catalogue = readCatalogue(root);
  readCitations(root, catalogue);
  const rows = completeCatalogue(catalogue);
  const document =
    /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
      original
    );
  assert.deepEqual(
    rows,
    document.records.map((record) => record.taxonomy_record),
  );
  return { document, rows };
}

module.exports = { loadProfileFixture };
