// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — complete original/current reviewed profile consumer.
"use strict";

/** Whole reviewed profile admission shared by Node and classic scripts. */
var AtlasTaxonomyReviewedProfiles = (() => {
  /** @type {import("./author-review-contracts").AuthorReviewValues} */
  const values =
    typeof module !== "undefined"
      ? require("./author-review-values.js")
      : globalThis.AtlasAuthorReviewValues;
  const author =
    typeof module !== "undefined"
      ? require("./taxonomy-author-review.js")
      : globalThis.AtlasTaxonomyAuthorReview;
  /**
   * Compare complete parsed JSON relationships without treating key order as meaning.
   * @param {unknown} value Actual product before equality checks.
   * @param {unknown} expected Owning-validated original or recomposed current value.
   * @returns {boolean} Every original member and ordered array cell matches.
   */
  function same(value, expected) {
    if (Array.isArray(expected))
      return (
        Array.isArray(value) &&
        value.length === expected.length &&
        expected.every((item, index) => same(value[index], item))
      );
    if (expected !== null && typeof expected === "object") {
      if (value === null || typeof value !== "object" || Array.isArray(value))
        return false;
      /** @type {Record<string,unknown>} */
      const left = /** @type {Record<string,unknown>} */ (value);
      /** @type {Record<string,unknown>} */
      const right = /** @type {Record<string,unknown>} */ (expected);
      return (
        Object.keys(left).length === Object.keys(right).length &&
        Object.keys(right).every(
          (key) => Object.hasOwn(left, key) && same(left[key], right[key]),
        )
      );
    }
    return value === expected;
  }
  /**
   * Admit the complete current catalogue with separate exact original and author contexts.
   * @param {unknown} input Actual whole product before admission.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument["inputs"]} expectedInputs Explicit trusted source bindings from the owning snapshot.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Complete owning-validated original profile.
   * @returns {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} Whole admitted product without rewritten originals or acceptance flags.
   * @throws {Error} Any version, shape, source binding, original or current record differs.
   */
  function read(input, expectedInputs, original) {
    values.object(input, [
      "schema_version",
      "record_count",
      "metadata_license",
      "source_rights",
      "inputs",
      "original_profiles",
      "author_reviews",
      "records",
    ]);
    if (
      input.schema_version !== "atlas-reviewed-profiles-2.1.0" ||
      input.record_count !== original.record_count ||
      input.metadata_license !== "AGPL-3.0-or-later" ||
      input.source_rights !== "catalogue-only; original not redistributed"
    )
      throw new Error("Reviewed profile version, count or rights are invalid");
    const keys = [
      "taxonomy_sha256",
      "citations_sha256",
      "audit_sha256",
      "original_profiles_sha256",
      "author_reviews_sha256",
    ];
    values.object(input.inputs, keys);
    const inputs = input.inputs;
    if (
      !same(input.inputs, expectedInputs) ||
      !["taxonomy_sha256", "citations_sha256", "audit_sha256"].every(
        (key) =>
          inputs[/** @type {keyof typeof expectedInputs} */ (key)] ===
          original.inputs[/** @type {keyof typeof original.inputs} */ (key)],
      )
    )
      throw new Error("Reviewed profile source hashes differ");
    if (!same(input.original_profiles, original))
      throw new Error("Reviewed profile changed its original context");
    const assessment = author.read(input.author_reviews, original);
    if (!same(input.records, author.project(assessment, original)))
      throw new Error(
        "Reviewed profile current rows differ from explicit revisions",
      );
    return /** @type {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} */ (
      input
    );
  }
  /**
   * Select one current/original profile only after complete catalogue admission.
   * @param {unknown} input Whole product rather than an unchecked selected row.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument["inputs"]} expectedInputs Explicit source bindings from the owning snapshot.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Owning-validated complete original profile.
   * @param {string} entryId Stable original catalogue identity.
   * @returns {{taxonomy_record:import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow,original_profile:import("./taxonomy-evidence-profile.js").AtlasEvidenceProfile,author_review:import("./taxonomy-author-review.js").AuthorEntry}} Independent selected contexts with no lost source or history.
   * @throws {Error} Whole admission or the selected identity fails.
   */
  function readProfile(input, expectedInputs, original, entryId) {
    const document = read(input, expectedInputs, original);
    values.identity(entryId);
    const index = document.records.findIndex((row) => row.id === entryId);
    if (index < 0) throw new Error("Reviewed profile selection is absent");
    return structuredClone({
      taxonomy_record: document.records[index],
      original_profile: document.original_profiles.records[index],
      author_review: document.author_reviews.records[index],
    });
  }
  return Object.freeze({ read, readProfile });
})();
globalThis.AtlasTaxonomyReviewedProfiles = AtlasTaxonomyReviewedProfiles;
if (typeof module !== "undefined")
  module.exports = AtlasTaxonomyReviewedProfiles;
