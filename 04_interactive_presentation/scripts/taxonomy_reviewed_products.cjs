// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-preserving reviewed profile product composition.
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { isDeepStrictEqual } = require("node:util");
const author = require("../taxonomy-author-review.js");

/**
 * Whole reviewed projection retaining the frozen original and separate author decisions.
 * @typedef {object} ReviewedProfileDocument
 * @property {"atlas-reviewed-profiles-2.1.0"} schema_version Explicit whole-document version.
 * @property {number} record_count Complete original entry count.
 * @property {"AGPL-3.0-or-later"} metadata_license Authored metadata licence.
 * @property {"catalogue-only; original not redistributed"} source_rights Separate publisher body boundary.
 * @property {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument["inputs"] & {original_profiles_sha256:string,author_reviews_sha256:string}} inputs Actual frozen source byte bindings.
 * @property {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument} original_profiles Complete original source-bound profile and history.
 * @property {import("../taxonomy-author-review.js").AuthorReviewDocument} author_reviews Complete separately admitted author assessment.
 * @property {import("./taxonomy_export_inputs.cjs").TaxonomyRow[]} records Complete independently cloned revised rows.
 */

/**
 * Prepare both versioned products from actual complete original and author inputs.
 * The original profile is already admitted by its owning Python producer. Both
 * source bytes are checked again before anything can reach product publication.
 * @param {string} repositoryRoot Complete candidate with original source/profile inputs.
 * @param {string} snapshot Explicit original taxonomy hash from the owning export.
 * @param {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Owning-validated complete original profile.
 * @param {string} reviewsFile Whole author input selected by the owning exporter.
 * @returns {Map<string,string>} Both fully composed JSON and classic-script products.
 * @throws {Error} Inputs, validation, bindings, source immutability or output aliases fail.
 */
function reviewedProducts(repositoryRoot, snapshot, original, reviewsFile) {
  const profilePath = path.join(
    repositoryRoot,
    "metadata/evidence_profiles/profiles.json",
  );
  const inputPath = path.resolve(reviewsFile);
  const data = path.join(repositoryRoot, "04_interactive_presentation/data");
  for (const name of [
    "taxonomy-expanded.sources.tsv",
    "taxonomy-audit.json",
    "taxonomy-audit.js",
    "taxonomy-evidence-profiles.json",
    "taxonomy-evidence-profiles.js",
    "taxonomy-reviewed-profiles.json",
    "taxonomy-reviewed-profiles.js",
  ]) {
    const target = path.join(data, name);
    if (
      path.resolve(target) === inputPath ||
      (fs.existsSync(target) &&
        fs.realpathSync(target) === fs.realpathSync(inputPath))
    )
      throw new Error("Reviewed evidence: product cannot replace author input");
  }
  const profileBytes = fs.readFileSync(profilePath);
  const reviewBytes = fs.readFileSync(inputPath);
  const validated = spawnSync(
    process.env.ATLAS_PYTHON || "python3",
    [
      path.resolve(
        __dirname,
        "../../metadata/evidence_profiles/review_contract.py",
      ),
      "--root",
      repositoryRoot,
      "--snapshot",
      snapshot,
      "--reviews",
      inputPath,
    ],
    { encoding: "utf8", timeout: 45000, maxBuffer: 8 * 1024 * 1024 },
  );
  if (validated.status !== 0)
    throw new Error("Reviewed evidence: complete author admission failed");
  /** @type {unknown} */
  const parsed = JSON.parse(validated.stdout);
  if (
    !profileBytes.equals(fs.readFileSync(profilePath)) ||
    !reviewBytes.equals(fs.readFileSync(inputPath)) ||
    !isDeepStrictEqual(JSON.parse(profileBytes.toString("utf8")), original) ||
    !isDeepStrictEqual(JSON.parse(reviewBytes.toString("utf8")), parsed)
  )
    throw new Error("Reviewed evidence: source changed during composition");
  const assessment = author.read(parsed, original);
  /** @type {ReviewedProfileDocument} */
  const document = {
    schema_version: "atlas-reviewed-profiles-2.1.0",
    record_count: original.record_count,
    metadata_license: "AGPL-3.0-or-later",
    source_rights: "catalogue-only; original not redistributed",
    inputs: {
      ...original.inputs,
      original_profiles_sha256: createHash("sha256")
        .update(profileBytes)
        .digest("hex"),
      author_reviews_sha256: createHash("sha256")
        .update(reviewBytes)
        .digest("hex"),
    },
    original_profiles: original,
    author_reviews: assessment,
    records: author.project(assessment, original),
  };
  const serialized = JSON.stringify(document, null, 2) + "\n";
  return new Map([
    ["taxonomy-reviewed-profiles.json", serialized],
    [
      "taxonomy-reviewed-profiles.js",
      `// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — generated original and completed author profiles.
window.REACTOR_TAXONOMY_REVIEWED_PROFILE_INPUTS = Object.freeze(${JSON.stringify(document.inputs, null, 2)});\nwindow.REACTOR_TAXONOMY_REVIEWED_PROFILES = ${serialized.trimEnd()};\n`,
    ],
  ]);
}

module.exports = { reviewedProducts };
