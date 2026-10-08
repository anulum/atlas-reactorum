// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound original history profile fixtures.
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");

/**
 * Bind the original release profile product to the complete source validators.
 * Member order is retained because history hashes the original JSON representation.
 * @param {string} root Actual repository holding original profile source and product.
 * @returns {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument} Original source-validated release product.
 * @throws {Error} The complete product differs from its source-validated document or changes during loading.
 */
function loadHistoryProfiles(root) {
  const { document } = loadProfileFixture(root);
  const filename = path.join(
    root,
    "04_interactive_presentation/data/taxonomy-evidence-profiles.json",
  );
  const bytes = fs.readFileSync(filename);
  /** @type {unknown} */
  const product = JSON.parse(bytes.toString("utf8"));
  assert.equal(JSON.stringify(product), JSON.stringify(document));
  assert.deepEqual(fs.readFileSync(filename), bytes);
  return /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
    product
  );
}

/**
 * Select the original non-numeric parameter before changing its explanation.
 * @param {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceProfile} profile Actual fixture profile.
 * @returns {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasMissingParameter} Existing explicit missing-value record.
 */
function missingParameter(profile) {
  const parameter = profile.parameters[0];
  assert.ok(parameter.state !== "known");
  return parameter;
}

module.exports = { loadHistoryProfiles, missingParameter };
