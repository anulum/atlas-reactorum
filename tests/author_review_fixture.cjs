// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual whole source assessment after original native admission.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");
/**
 * Load the real whole assessment and baseline through both owning Python CLIs.
 * @param {string} root Complete actual repository or candidate.
 * @returns {{baseline:import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument,review:import("../04_interactive_presentation/taxonomy-author-review.js").AuthorReviewDocument}} Original complete inputs after their owning native admission.
 * @throws {Error} Input custody changes, validation fails or the whole input is absent.
 */
function loadAuthorReviewFixture(root) {
  const baseline = loadProfileFixture(root).document;
  const input =
    process.env.ATLAS_AUTHOR_REVIEW_INPUT ||
    path.join(root, "metadata/evidence_profiles/author_reviews.json");
  const before = fs.readFileSync(input);
  const output = execFileSync(
    process.env.ATLAS_PYTHON || "python3",
    [
      path.join(root, "metadata/evidence_profiles/review_contract.py"),
      "--root",
      root,
      "--snapshot",
      baseline.inputs.taxonomy_sha256,
      "--reviews",
      input,
    ],
    { encoding: "utf8", timeout: 45000, maxBuffer: 8 * 1024 * 1024 },
  );
  /** @type {unknown} */
  const original = JSON.parse(before.toString("utf8"));
  /** @type {unknown} */
  const admitted = JSON.parse(output);
  assert.deepEqual(original, admitted);
  assert.deepEqual(fs.readFileSync(input), before);
  return {
    baseline,
    review:
      /** @type {import("../04_interactive_presentation/taxonomy-author-review.js").AuthorReviewDocument} */ (
        admitted
      ),
  };
}
module.exports = { loadAuthorReviewFixture };
