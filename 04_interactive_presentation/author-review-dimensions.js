// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound classification and attained development.
"use strict";

/** Admission of overlapping facets and scoped development without independent acceptance. */
var AtlasAuthorReviewDimensions = (() => {
  /** @type {import("./author-review-contracts").AuthorReviewValues} */
  const values =
    typeof module !== "undefined"
      ? require("./author-review-values.js")
      : globalThis.AtlasAuthorReviewValues;
  const axes = new Set([
    "entity-role",
    "reaction",
    "geometry",
    "fuel-state",
    "coolant",
    "moderator",
    "circulation",
    "confinement",
    "drive",
    "process",
    "application",
    "integration",
  ]);
  /**
   * Bind one dimension to nonempty entry-owned claims or observations.
   * @param {Record<string,unknown>} item Shape-checked facet or attained assessment.
   * @param {Set<string>} claims Original claim identities belonging to this entry.
   * @param {Map<string,import("./taxonomy-author-review.js").AuthorObservation>} observations Already admitted observations belonging to this entry.
   * @returns {string[]} Original observation reference order after complete checks.
   * @throws {Error} Evidence is absent, unbound or belongs to another entry.
   */
  function references(item, claims, observations) {
    values.strings(item.claim_ids);
    values.strings(item.observation_ids);
    if (!item.claim_ids.length && !item.observation_ids.length)
      throw new Error("Author dimension has no supporting evidence");
    if (
      item.claim_ids.some((id) => !claims.has(id)) ||
      item.observation_ids.some((id) => !observations.has(id))
    )
      throw new Error(
        "Author dimension refers to another or absent entry evidence",
      );
    return item.observation_ids;
  }
  /**
   * Admit actual classification axes and development through the whole author reader.
   * @param {{facets:unknown,development_assessments:unknown}} input Parsed dimensions before admission.
   * @param {string} category Admitted primary entity role.
   * @param {Set<string>} claims Original entry-owned claim identities.
   * @param {import("./taxonomy-author-review.js").AuthorObservation[]} observed Already admitted entry observations.
   * @returns {void} All dimensions checked before the whole reader returns.
   * @throws {Error} Shape, evidence ownership, role or attained evidence is invalid.
   */
  function validate(input, category, claims, observed) {
    const observations = new Map(observed.map((item) => [item.id, item]));
    values.array(input.facets);
    values.array(input.development_assessments);
    /** @type {Set<string>} */
    const pairs = new Set();
    for (const facet of input.facets) {
      values.object(facet, [
        "axis",
        "value",
        "assessment",
        "scope",
        "claim_ids",
        "observation_ids",
      ]);
      values.text(facet.axis);
      values.identity(facet.value);
      values.text(facet.assessment);
      values.text(facet.scope);
      if (!axes.has(facet.axis))
        throw new Error("Author classification axis is invalid");
      references(facet, claims, observations);
      const pair = `${facet.axis}:${facet.value}`;
      if (pairs.has(pair))
        throw new Error("Author classification duplicates an axis and value");
      pairs.add(pair);
    }
    if (!pairs.has(`entity-role:${category}`))
      throw new Error("Author classification omits its declared primary role");
    /** @type {Set<string>} */
    const ids = new Set();
    for (const item of input.development_assessments) {
      values.object(item, [
        "id",
        "stage",
        "evidence_object",
        "assessment",
        "scope",
        "claim_ids",
        "observation_ids",
      ]);
      values.identity(item.id);
      for (const key of ["stage", "evidence_object", "assessment", "scope"])
        values.text(item[key]);
      if (
        !["laboratory", "pilot", "industrial"].includes(
          /** @type {string} */ (item.stage),
        ) ||
        !["experiment", "simulation", "operation"].includes(
          /** @type {string} */ (item.evidence_object),
        )
      )
        throw new Error(
          "Author development stage or evidence object is invalid",
        );
      const referenced = references(item, claims, observations);
      if (ids.has(item.id))
        throw new Error("Author development duplicates an assessment identity");
      ids.add(item.id);
      if (
        !referenced.length ||
        referenced.some((ref) => {
          const observation =
            /** @type {import("./taxonomy-author-review.js").AuthorObservation} */ (
              observations.get(ref)
            );
          return (
            observation.temporal_role !== "attained" ||
            observation.topic !== "maturity"
          );
        })
      )
        throw new Error(
          "Attained development requires attained maturity observations",
        );
      if (
        referenced.some(
          (ref) =>
            /** @type {import("./taxonomy-author-review.js").AuthorObservation} */ (
              observations.get(ref)
            ).evidence_object !== item.evidence_object,
        )
      )
        throw new Error(
          "Attained development differs from its source evidence object",
        );
      if (
        item.evidence_object !== "operation" &&
        ["pilot", "industrial"].includes(/** @type {string} */ (item.stage))
      )
        throw new Error(
          "Pilot or industrial development requires operation evidence",
        );
    }
  }
  return Object.freeze({ validate });
})();
globalThis.AtlasAuthorReviewDimensions = AtlasAuthorReviewDimensions;
if (typeof module !== "undefined") module.exports = AtlasAuthorReviewDimensions;
