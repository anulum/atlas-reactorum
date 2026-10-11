// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — separate current author assessment and original source context.
"use strict";

/** Presentation of admitted author decisions without independent entry acceptance. */
var AtlasTaxonomyReviewedPresentation = (() => {
  const reader =
    typeof module !== "undefined"
      ? require("./taxonomy-reviewed-profiles.js")
      : globalThis.AtlasTaxonomyReviewedProfiles;
  const escape = globalThis.AtlasPresentationText.escape;
  /**
   * Select every original/author supporting source from the admitted complete registry.
   * @param {ReturnType<typeof reader.readProfile>} selected All three independent selected contexts.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} document Admitted whole reviewed product.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Complete owning-validated original profile.
   * @returns {import("./scripts/taxonomy_citations.cjs").CitationSource[]} Original metadata order followed by admitted additional sources.
   */
  function supportingSources(selected, document, original) {
    const used = new Set(
      selected.original_profile.claims.map((claim) => claim.citation.source_id),
    );
    for (const field of Object.values(selected.author_review.fields))
      for (const identity of field.source_ids) used.add(identity);
    for (const observation of selected.author_review.observations)
      used.add(observation.source_id);
    return [
      ...original.sources,
      ...document.author_reviews.additional_sources,
    ].filter((source) => used.has(source.id));
  }
  /**
   * Show actual source acquisition without assigning an unknown retrieval date.
   * @param {import("./scripts/taxonomy_citations.cjs").CitationSource} source Actual admitted source metadata.
   * @returns {string} Recorded UTC capture time or an explicit unknown-date label.
   */
  function captureText(source) {
    return source.captured_at === null
      ? "Original retrieval date unknown"
      : source.captured_at;
  }
  /**
   * Export the selected current/original contexts and every source they reference.
   * @param {unknown} input Whole actual reviewed product before admission.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument["inputs"]} expectedInputs Explicit owning-produced snapshot bindings.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Whole owning-validated original profile.
   * @param {string} entryId Stable selected catalogue identity.
   * @returns {string} Complete single-entry JSON with separate original and author contexts.
   * @throws {Error} Whole admission or the selected identity fails.
   */
  function exportProfile(input, expectedInputs, original, entryId) {
    const selected = reader.readProfile(
      input,
      expectedInputs,
      original,
      entryId,
    );
    const document =
      /** @type {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} */ (
        input
      );
    return entryJson(document, selected, original);
  }
  /**
   * Encode already admitted contexts without repeating whole admission within one call.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} document Admitted whole product.
   * @param {ReturnType<typeof reader.readProfile>} selected Independent contexts from the owning public reader.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Complete owning-validated original profile.
   * @returns {string} Versioned single-entry JSON with every supporting source.
   */
  function entryJson(document, selected, original) {
    return (
      JSON.stringify(
        {
          schema_version: "atlas-entry-reviewed-profile-2.1.0",
          metadata_license: document.metadata_license,
          source_rights: document.source_rights,
          inputs: document.inputs,
          selected_entry_id: selected.taxonomy_record.id,
          author_review_context: {
            author: document.author_reviews.author,
            reviewed_on: document.author_reviews.reviewed_on,
          },
          ...selected,
          sources: supportingSources(selected, document, original),
        },
        null,
        2,
      ) + "\n"
    );
  }
  /**
   * Retain declared temporal precision and an explicit unknown date.
   * @param {import("./taxonomy-author-review.js").AuthorObservation["event_date"]} date Actual admitted event or publication metadata.
   * @returns {string} Original date and precision or an unknown-date label.
   */
  function dateText(date) {
    return date.value === null
      ? "Unknown"
      : `${date.value} (${date.precision})`;
  }
  /**
   * Render all selected field decisions, scoped facets, stages and source observations.
   * @param {unknown} input Actual complete reviewed product before admission.
   * @param {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument["inputs"]} expectedInputs Explicit source bindings from the owning static snapshot.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} original Complete admitted original profile.
   * @param {string} entryId Stable selected identity, preserving original history.
   * @returns {string} Accessible disclosure controls and an explicit selected-profile download.
   * @throws {Error} The whole catalogue or selected entry is inconsistent.
   */
  function render(input, expectedInputs, original, entryId) {
    const selected = reader.readProfile(
      input,
      expectedInputs,
      original,
      entryId,
    );
    const document =
      /** @type {import("./scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} */ (
        input
      );
    const review = selected.author_review;
    const sources = new Map(
      [...original.sources, ...document.author_reviews.additional_sources].map(
        (source) => [source.id, source],
      ),
    );
    const fields = Object.entries(review.fields)
      .map(
        ([name, field]) =>
          `<li><h4>${escape(name.replaceAll("_", " "))}: ${escape(field.disposition.replaceAll("-", " "))}</h4><p>${escape(field.assessment)}</p><p>Original catalogue value: ${escape(JSON.stringify(field.original_value))}</p><p>Current catalogue value: ${escape(JSON.stringify(selected.taxonomy_record[/** @type {keyof typeof selected.taxonomy_record} */ (name)]))}</p><p>Original claim references: ${escape(field.claim_ids.join(", "))}. Source references: ${escape(field.source_ids.join(", "))}.</p></li>`,
      )
      .join("");
    const facets = review.facets
      .map(
        (facet) =>
          `<li><strong>${escape(facet.axis)}: ${escape(facet.value)}</strong><p>${escape(facet.assessment)}</p><p>Scope: ${escape(facet.scope)}</p><p>Original claims: ${escape(facet.claim_ids.join(", "))}. Observations: ${escape(facet.observation_ids.join(", "))}.</p></li>`,
      )
      .join("");
    const stages =
      review.development_assessments
        .map(
          (stage) =>
            `<li><strong>${escape(stage.stage)} — ${escape(stage.evidence_object)}</strong><p>${escape(stage.assessment)}</p><p>Scope: ${escape(stage.scope)}</p><p>Original claims: ${escape(stage.claim_ids.join(", "))}. Attained observations: ${escape(stage.observation_ids.join(", "))}.</p></li>`,
        )
        .join("") ||
      "<li>No attained stage has been assessed here; consult the preserved original context.</li>";
    const observations =
      review.observations
        .map((observation) => {
          // Whole admission already binds every observation to this complete registry.
          const source =
            /** @type {import("./scripts/taxonomy_citations.cjs").CitationSource} */ (
              sources.get(observation.source_id)
            );
          const locator = observation.pdf_pages.length
            ? `Printed page(s) ${observation.printed_pages.join(", ")}; PDF page(s) ${observation.pdf_pages.join(", ")} (one-based).`
            : "HTML/XML section locator.";
          return `<li><strong>${escape(observation.topic)} — ${escape(observation.evidence_object)} / ${escape(observation.temporal_role)}</strong><p>${escape(observation.statement)}</p><p>Scope: ${escape(observation.scope)}</p><p>Event: ${escape(dateText(observation.event_date))}. Publication: ${escape(dateText(observation.published_date))}.</p><p><a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">${escape(source.title)}</a> — ${escape(observation.section)}. ${escape(locator)}</p><p>Source capture: ${escape(captureText(source))}. Source rights: ${escape(source.access)}.</p></li>`;
        })
        .join("") ||
      "<li>No additional source-specific observations recorded for this entry.</li>";
    const sourceCards = supportingSources(selected, document, original)
      .map(
        (source) =>
          `<li><a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">${escape(source.title)}</a><p>Source reference: ${escape(source.id)}. SHA-256: ${escape(source.sha256)}</p><p>Source capture: ${escape(captureText(source))}. Method: ${escape(source.capture_method)}. Source rights: ${escape(source.access)}.</p></li>`,
      )
      .join("");
    const download =
      "data:application/json;charset=utf-8," +
      encodeURIComponent(entryJson(document, selected, original)).replaceAll(
        "'",
        "%27",
      );
    return `<section class="author-assessment" aria-label="Dated author assessment"><h3>Author assessment — ${escape(document.author_reviews.reviewed_on)}</h3><p>By ${escape(document.author_reviews.author)}. Classification facets and attained stages are source-scoped author assessments. Author review covers all original fields and selected sources. Unknown and unsupported outcomes remain explicit. Independent entry acceptance has not been recorded. Current activity is unknown.</p><details class="author-fields"><summary>All ${Object.keys(review.fields).length} field assessments and original values</summary><ul>${fields}</ul></details><details class="author-facets"><summary>Source-scoped classification facets</summary><ul>${facets}</ul></details><details class="author-development"><summary>Attained stages and evidence boundaries</summary><ul>${stages}</ul></details><details class="author-observations"><summary>Source observations, locators and dates</summary><ul>${observations}</ul></details><details class="author-sources"><summary>Sources supporting the original and current profiles</summary><ul>${sourceCards}</ul></details><p><a class="reviewed-profile-download" href="${escape(download)}" download="${escape(entryId)}-reviewed-profile.json">Download current and original profile (JSON)</a></p></section>`;
  }
  return Object.freeze({ render, exportProfile });
})();
globalThis.AtlasTaxonomyReviewedPresentation =
  AtlasTaxonomyReviewedPresentation;
if (typeof module !== "undefined")
  module.exports = AtlasTaxonomyReviewedPresentation;
