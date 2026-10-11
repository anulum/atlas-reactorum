// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound whole-catalogue author assessment reader.
"use strict";

/**
 * A dated source observation before any independent entry acceptance.
 * @typedef {object} AuthorObservation
 * @property {string} id Stable observation identity.
 * @property {string} source_id Source registry identity.
 * @property {string} topic Classification, maturity, evidence or source consistency.
 * @property {"experiment"|"simulation"|"operation"|"publication"|"proposal"} evidence_object Explicit source evidence object.
 * @property {string} statement Source-specific authored statement.
 * @property {string} scope Applicability boundary.
 * @property {string} section Exact source section.
 * @property {number[]} pdf_pages Original PDF locators.
 * @property {string[]} printed_pages Original printed labels.
 * @property {{value:string|null,precision:"year"|"month"|"day"|null}} event_date Explicit event precision.
 * @property {AuthorObservation["event_date"]} published_date Separate publication precision.
 * @property {"attained"|"publication"|"forecast"|"unspecified"} temporal_role Source-specific temporal role.
 */
/**
 * Field assessment retaining its original context and supporting references.
 * @typedef {{original_value:unknown,disposition:"editorial"|"source-qualified"|"correction-required"|"unsupported"|"unscored"|"context-only",assessment:string,claim_ids:string[],source_ids:string[]}} AuthorField
 */
/**
 * Source-bound facet preserving overlapping axes.
 * @typedef {{axis:string,value:string,assessment:string,scope:string,claim_ids:string[],observation_ids:string[]}} AuthorFacet
 */
/**
 * Scoped attained development with an explicit evidence object.
 * @typedef {{id:string,stage:"laboratory"|"pilot"|"industrial",evidence_object:"experiment"|"simulation"|"operation",assessment:string,scope:string,claim_ids:string[],observation_ids:string[]}} AuthorDevelopment
 */
/**
 * Explicit source-supported correction, leaving the original value separately retained.
 * @typedef {{field:"name"|"kind"|"maturity"|"evidence"|"principle"|"strength"|"challenge"|"temp"|"mode"|"evidence_scope",value:string}} AuthorRevision
 */
/**
 * Whole entry author assessment distinct from independent acceptance.
 * @typedef {{entry_id:string,entity_category:string,fields:Record<string,AuthorField>,observations:AuthorObservation[],revisions:AuthorRevision[],facets:AuthorFacet[],development_assessments:AuthorDevelopment[],current_activity:"unknown",review_scope:"all-original-fields-and-selected-sources",review_basis:"author-source-inspection",complete_entry_review:true,independent_review:null}} AuthorEntry
 */
/**
 * Source-admitted whole author assessment preserving its original baseline.
 * @typedef {{schema_version:"atlas-author-review-1.1.0",author:"Arcane Sapience",reviewed_on:string,baseline_inputs:import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument["inputs"],additional_sources:import("./scripts/taxonomy_citations.cjs").CitationSource[],records:AuthorEntry[]}} AuthorReviewDocument
 */

/** Browser and Node facade admitting every original field before returning any entry. */
var AtlasTaxonomyAuthorReview = (() => {
  /** @type {import("./author-review-contracts").AuthorReviewValues} */
  const values =
    typeof module !== "undefined"
      ? require("./author-review-values.js")
      : globalThis.AtlasAuthorReviewValues;
  const dimensions =
    typeof module !== "undefined"
      ? require("./author-review-dimensions.js")
      : globalThis.AtlasAuthorReviewDimensions;
  const revisions =
    typeof module !== "undefined"
      ? require("./author-review-revisions.js")
      : globalThis.AtlasAuthorReviewRevisions;
  const categories = new Set([
    "architecture",
    "subtype",
    "development-class",
    "geometry",
    "configuration",
    "operating-mode",
    "ignition-scheme",
    "device",
    "process-class",
    "system-integration",
    "application-architecture",
    "reaction-mechanism",
    "claim-class",
  ]);
  const dispositions = new Set([
    "editorial",
    "source-qualified",
    "correction-required",
    "unsupported",
    "unscored",
    "context-only",
  ]);
  const editorial = new Set([
    "id",
    "domain",
    "family",
    "parent",
    "parent_id",
    "source_ids",
    "source_urls",
    "reviewed_on",
    "source_audit",
  ]);
  /**
   * Preserve actual original scalars and ordered reference arrays without coercion.
   * @param {unknown} current Assessment value before admission.
   * @param {unknown} original Source-validated original value.
   * @returns {boolean} Exact type/value/reference-order equality.
   */
  function sameValue(current, original) {
    if (Array.isArray(current) && Array.isArray(original))
      return (
        current.length === original.length &&
        current.every((value, index) => sameValue(value, original[index]))
      );
    return current === original;
  }
  /**
   * Require original input hashes without treating object member order as meaning.
   * @param {unknown} input Candidate hash object.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} baseline Owning-validated complete baseline.
   * @returns {void} Complete hash binding checked before field admission.
   * @throws {Error} A binding differs or its shape is invalid.
   */
  function inputHashes(input, baseline) {
    const keys = ["taxonomy_sha256", "citations_sha256", "audit_sha256"];
    values.object(input, keys);
    if (
      keys.some(
        (key) =>
          input[key] !==
          baseline.inputs[/** @type {keyof typeof baseline.inputs} */ (key)],
      )
    )
      throw new Error("Author review baseline hashes differ");
  }
  /**
   * Bind each actual source observation to its locators and declared temporal role.
   * @param {unknown} input Parsed observations.
   * @param {Map<string,import("./scripts/taxonomy_citations.cjs").CitationSource>} sources Complete source registry.
   * @param {string} reviewed Current author assessment day.
   * @param {Set<string>} ids Previously encountered global observation identities.
   * @param {Set<string>} used Sources used by real fields or observations.
   * @returns {void} Entire collection checked without rewriting observations.
   * @throws {Error} An observation, locator, date or source binding is invalid.
   */
  function observations(input, sources, reviewed, ids, used) {
    values.array(input);
    for (const item of input) {
      values.object(item, [
        "id",
        "source_id",
        "topic",
        "statement",
        "scope",
        "section",
        "pdf_pages",
        "printed_pages",
        "event_date",
        "published_date",
        "temporal_role",
        "evidence_object",
      ]);
      values.identity(item.id);
      if (ids.has(item.id))
        throw new Error("Author review duplicates an observation identity");
      ids.add(item.id);
      values.text(item.source_id);
      const source = sources.get(item.source_id);
      if (!source)
        throw new Error("Author observation refers to an unknown source");
      for (const key of ["statement", "scope", "section"])
        values.text(item[key]);
      values.text(item.topic);
      values.text(item.temporal_role);
      values.text(item.evidence_object);
      if (
        ![
          "experiment",
          "simulation",
          "operation",
          "publication",
          "proposal",
        ].includes(item.evidence_object)
      )
        throw new Error("Author observation evidence object is invalid");
      if (
        ![
          "classification",
          "maturity",
          "evidence",
          "source-consistency",
        ].includes(item.topic) ||
        !["attained", "publication", "forecast", "unspecified"].includes(
          item.temporal_role,
        )
      )
        throw new Error("Author observation topic or temporal role is invalid");
      values.array(item.pdf_pages);
      values.array(item.printed_pages);
      if (
        new Set(item.pdf_pages).size !== item.pdf_pages.length ||
        item.pdf_pages.some(
          (page) =>
            typeof page !== "number" || !Number.isInteger(page) || page < 1,
        )
      )
        throw new Error("Author observation has invalid PDF pages");
      for (const label of item.printed_pages) values.text(label);
      if (source.format === "pdf") {
        if (
          !item.pdf_pages.length ||
          item.pdf_pages.length !== item.printed_pages.length ||
          item.pdf_pages.some(
            (page) => /** @type {number} */ (page) > source.page_count,
          )
        )
          throw new Error("Author observation has an invalid PDF locator");
      } else if (item.pdf_pages.length || item.printed_pages.length)
        throw new Error("Author observation has pages for a non-PDF source");
      const event = values.dateBounds(item.event_date);
      const published = values.dateBounds(item.published_date);
      if (item.temporal_role === "attained" && event && event[0] > reviewed)
        throw new Error("A future event cannot establish attained maturity");
      if (
        item.temporal_role === "attained" &&
        event &&
        published &&
        event[0] > published[1]
      )
        throw new Error("An attained event postdates its reported publication");
      if (published && published[0] > reviewed)
        throw new Error("A source publication postdates its assessment");
      if (
        published &&
        source.captured_at !== null &&
        published[0] > source.captured_at.slice(0, 10)
      )
        throw new Error("A source publication postdates its acquisition");
      used.add(source.id);
    }
  }
  /**
   * Admit a complete author assessment against its owning-validated original baseline.
   * This checks the entire input before returning any record; it grants no source rights or independent entry acceptance.
   * @param {unknown} input Actual parsed author assessment before wire/semantic admission.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} baseline Whole original profile after its owning producer validation.
   * @returns {AuthorReviewDocument} Exact admitted assessment without value/date inference.
   * @throws {Error} Any schema, original field, claim/source or temporal binding fails.
   */
  function read(input, baseline) {
    values.object(input, [
      "schema_version",
      "author",
      "reviewed_on",
      "baseline_inputs",
      "additional_sources",
      "records",
    ]);
    if (
      input.schema_version !== "atlas-author-review-1.1.0" ||
      input.author !== "Arcane Sapience"
    )
      throw new Error("Author review version or author is invalid");
    values.day(input.reviewed_on);
    inputHashes(input.baseline_inputs, baseline);
    values.array(input.records);
    values.array(input.additional_sources);
    if (
      baseline.schema_version !== "1.0.0" ||
      !baseline.records.length ||
      baseline.record_count !== baseline.records.length ||
      input.records.length !== baseline.records.length
    )
      throw new Error(
        "Author review must cover the complete catalogue in order",
      );
    /** @type {Map<string,import("./scripts/taxonomy_citations.cjs").CitationSource>} */
    const sources = new Map();
    for (const raw of [...baseline.sources, ...input.additional_sources]) {
      const source = values.source(raw);
      if (sources.has(source.id))
        throw new Error("Author review duplicates a source identity");
      if (
        source.captured_at !== null &&
        source.captured_at.slice(0, 10) > input.reviewed_on
      )
        throw new Error("Author review predates source acquisition");
      sources.set(source.id, source);
    }
    /** @type {Set<string>} */
    const ids = new Set();
    /** @type {Set<string>} */
    const used = new Set();
    for (const [index, item] of input.records.entries()) {
      values.object(item, [
        "entry_id",
        "entity_category",
        "revisions",
        "facets",
        "development_assessments",
        "fields",
        "observations",
        "current_activity",
        "review_scope",
        "review_basis",
        "complete_entry_review",
        "independent_review",
      ]);
      values.identity(item.entry_id);
      const original = baseline.records[index];
      if (item.entry_id !== original.entry_id || ids.has(item.entry_id))
        throw new Error(
          "Author review must cover the complete catalogue in order",
        );
      ids.add(item.entry_id);
      values.text(item.entity_category);
      if (
        !categories.has(item.entity_category) ||
        item.current_activity !== "unknown" ||
        item.review_scope !== "all-original-fields-and-selected-sources" ||
        item.review_basis !== "author-source-inspection" ||
        item.complete_entry_review !== true ||
        item.independent_review !== null
      )
        throw new Error(
          "Author review classification or acceptance is invalid",
        );
      const row = original.taxonomy_record;
      values.object(item.fields, Object.keys(row));
      const claims = new Map(
        original.claims.map((claim) => [claim.claim_id, claim.citation]),
      );
      if (
        original.claims.some(
          (claim) =>
            claim.citation.reviewed_on >
            /** @type {string} */ (input.reviewed_on),
        )
      )
        throw new Error(
          "Author review predates the original source inspection",
        );
      for (const [name, field] of Object.entries(item.fields)) {
        values.object(field, [
          "original_value",
          "disposition",
          "assessment",
          "claim_ids",
          "source_ids",
        ]);
        values.text(field.assessment);
        values.strings(field.claim_ids);
        values.strings(field.source_ids);
        const sourceIds = field.source_ids;
        values.text(field.disposition);
        if (!dispositions.has(field.disposition))
          throw new Error("Author field disposition is invalid");
        if (
          !sameValue(
            field.original_value,
            row[/** @type {keyof typeof row} */ (name)],
          )
        )
          throw new Error("Author review changed an original taxonomy value");
        if (
          field.claim_ids.some((id) => !claims.has(id)) ||
          field.source_ids.some((id) => !sources.has(id))
        )
          throw new Error(
            "Author field assessment has an unknown claim or source",
          );
        if (
          field.claim_ids.some(
            (id) =>
              !sourceIds.includes(
                /** @type {import("./scripts/taxonomy_citations.cjs").Citation} */ (
                  claims.get(id)
                ).source_id,
              ),
          )
        )
          throw new Error("Author field omits a cited claim's source");
        if (
          ["source-qualified", "correction-required"].includes(
            field.disposition,
          ) &&
          !field.source_ids.length
        )
          throw new Error(
            "Source-qualified assessment has no supporting source",
          );
        if (
          field.disposition === "context-only" &&
          !["temp", "mode"].includes(name)
        )
          throw new Error(
            "A scientific assertion cannot become descriptive context only",
          );
        if (field.disposition === "editorial" && !editorial.has(name))
          throw new Error(
            "A scientific field cannot become an editorial-only decision",
          );
        if (
          field.disposition === "unscored" &&
          (!["scale", "control"].includes(name) ||
            row[/** @type {keyof typeof row} */ (name)] !== null)
        )
          throw new Error(
            "An unscored assessment must preserve an absent score",
          );
        for (const id of field.source_ids) used.add(id);
      }
      revisions.validate(
        item.revisions,
        /** @type {Record<string,AuthorField>} */ (item.fields),
      );
    }
    /** @type {Set<string>} */
    const observationIds = new Set();
    for (const [index, item] of input.records.entries()) {
      values.object(item, [
        "entry_id",
        "entity_category",
        "revisions",
        "facets",
        "development_assessments",
        "fields",
        "observations",
        "current_activity",
        "review_scope",
        "review_basis",
        "complete_entry_review",
        "independent_review",
      ]);
      observations(
        item.observations,
        sources,
        input.reviewed_on,
        observationIds,
        used,
      );
      dimensions.validate(
        {
          facets: item.facets,
          development_assessments: item.development_assessments,
        },
        /** @type {string} */ (item.entity_category),
        new Set(baseline.records[index].claims.map((claim) => claim.claim_id)),
        /** @type {AuthorObservation[]} */ (item.observations),
      );
    }
    for (const raw of input.additional_sources) {
      const source = values.source(raw);
      if (!used.has(source.id))
        throw new Error("Author review includes an unused additional source");
    }
    return /** @type {AuthorReviewDocument} */ (input);
  }
  /**
   * Project a complete independent row collection after whole author admission.
   * @param {unknown} input Complete author source assessment before validation.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} baseline Owning-validated original whole profile.
   * @returns {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} Complete stable identities and original context with only explicit field revisions.
   * @throws {Error} Any entry, source, original value or revision fails admission.
   */
  function project(input, baseline) {
    const admitted = read(input, baseline);
    return admitted.records.map((record, index) => {
      const row = structuredClone(baseline.records[index].taxonomy_record);
      for (const revision of record.revisions)
        row[revision.field] = revision.value;
      return row;
    });
  }
  return Object.freeze({ read, project });
})();
globalThis.AtlasTaxonomyAuthorReview = AtlasTaxonomyAuthorReview;
if (typeof module !== "undefined") module.exports = AtlasTaxonomyAuthorReview;
