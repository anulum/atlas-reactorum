// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — explicit revisions preserving original identity and history.
"use strict";

/** Bind every proposed revision to its admitted field-specific correction. */
var AtlasAuthorReviewRevisions = (() => {
  /** @type {import("./author-review-contracts").AuthorReviewValues} */
  const values =
    typeof module !== "undefined"
      ? require("./author-review-values.js")
      : globalThis.AtlasAuthorReviewValues;
  const revisable = new Set([
    "name",
    "kind",
    "maturity",
    "evidence",
    "principle",
    "strength",
    "challenge",
    "temp",
    "mode",
    "evidence_scope",
  ]);
  /**
   * Admit exactly the explicitly corrected scientific text fields.
   * @param {unknown} input Parsed revisions before admission.
   * @param {Record<string,import("./taxonomy-author-review.js").AuthorField>} fields Already admitted complete field assessments and their original values.
   * @returns {void} Proposed values checked without changing original context.
   * @throws {Error} A revision alters history/identity, duplicates a field or lacks an admitted correction.
   */
  function validate(input, fields) {
    values.array(input);
    /** @type {Set<string>} */
    const seen = new Set();
    for (const item of input) {
      values.object(item, ["field", "value"]);
      values.text(item.field);
      values.text(item.value);
      if (!revisable.has(item.field))
        throw new Error("Author revision cannot change identity or history");
      if (seen.has(item.field))
        throw new Error("Author revision duplicates a field");
      seen.add(item.field);
      if (item.value === fields[item.field].original_value)
        throw new Error("Author revision must change its original value");
    }
    for (const [name, field] of Object.entries(fields)) {
      if ((field.disposition === "correction-required") !== seen.has(name))
        throw new Error(
          "Author revision differs from its field correction disposition",
        );
    }
  }
  return Object.freeze({ validate });
})();
globalThis.AtlasAuthorReviewRevisions = AtlasAuthorReviewRevisions;
if (typeof module !== "undefined") module.exports = AtlasAuthorReviewRevisions;
