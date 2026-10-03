// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound evidence profiles in taxonomy details
"use strict";

(() => {
  const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  const escape = value => String(value).replace(/[&<>"']/g, character => entities[character]);
  const fields = ["name", "kind", "family", "principle", "strength", "challenge", "maturity", "evidence", "source_urls"];
  const missingStates = new Set(["not_reported", "not_reviewed", "not_applicable", "disputed"]);

  /**
   * Read an explicitly selected entry from a complete validated snapshot.
   * @param {object} document Versioned whole-catalogue export.
   * @param {string} snapshot Explicit expected taxonomy SHA-256.
   * @param {string} entryId Stable selected catalogue identity.
   * @returns {object} Original profile retaining its bounded review disposition.
   * @throws {Error} On an unsupported, incomplete, duplicate or mismatched snapshot.
   */
  function readProfile(document, snapshot, entryId) {
    if (!document || document.schema_version !== "1.0.0" || document.inputs.taxonomy_sha256 !== snapshot) {
      throw new Error("Evidence profile snapshot is unavailable or mismatched");
    }
    if (!Array.isArray(document.records) || document.record_count !== document.records.length ||
        new Set(document.records.map(record => record.entry_id)).size !== document.record_count) {
      throw new Error("Evidence profile catalogue is incomplete or duplicated");
    }
    const profile = document.records.find(record => record.entry_id === entryId);
    if (!profile) throw new Error("Evidence profile entry does not exist");
    const review = profile.review_disposition;
    if (review.complete_entry_review !== false || review.classification.state !== "open" ||
        review.independent_review !== null || profile.entity_kind.decision !== "provisional") {
      throw new Error("Evidence profile cannot promote partial support to entry acceptance");
    }
    return profile;
  }

  /**
   * Export one selected profile together with every source supporting its claims.
   * @param {object} document Complete validated catalogue document.
   * @param {string} snapshot Explicit expected source hash.
   * @param {string} entryId Stable selected identity.
   * @returns {string} JSON with an explicit single-entry schema and original rights scope.
   */
  function exportProfile(document, snapshot, entryId) {
    const profile = readProfile(document, snapshot, entryId);
    const used = new Set(profile.claims.map(claim => claim.citation.source_id));
    const sources = document.sources.filter(source => used.has(source.id));
    if (sources.length !== used.size) throw new Error("Evidence profile source is missing");
    return JSON.stringify({
      schema_version: "atlas-entry-evidence-1.0.0",
      metadata_license: "AGPL-3.0-or-later",
      source_rights: "catalogue-only; original not redistributed",
      inputs: document.inputs,
      selected_entry_id: entryId,
      profile,
      sources,
    }, null, 2) + "\n";
  }

  /**
   * Render a profile against the actual selected taxonomy row.
   * @param {object} document Complete validated catalogue document.
   * @param {string} snapshot Explicit expected source hash.
   * @param {object} row Actual taxonomy row, including stable ID and bound values.
   * @returns {string} Accessible profile, exact citations and downloadable JSON.
   * @throws {Error} When the taxonomy, source support or parameter state is inconsistent.
   */
  function render(document, snapshot, row) {
    const profile = readProfile(document, snapshot, row.id);
    if (fields.some(field => JSON.stringify(profile.bound_values[field]) !== JSON.stringify(row[field]))) {
      throw new Error("Evidence profile differs from the selected taxonomy row");
    }
    if (Object.keys(profile.taxonomy_record).some(field => JSON.stringify(profile.taxonomy_record[field]) !== JSON.stringify(row[field]))) {
      throw new Error("Evidence profile taxonomy context differs");
    }
    const sources = new Map(document.sources.map(source => [source.id, source]));
    const citations = profile.claims.map(claim => {
      const citation = claim.citation;
      const source = sources.get(citation.source_id);
      if (!source || claim.claim_id !== citation.id || claim.original_statement !== citation.statement) {
        throw new Error("Evidence profile claim or source binding is inconsistent");
      }
      return { ...citation, source_title: source.title, source_url: source.url,
        source_sha256: source.sha256, source_capture_method: source.capture_method,
        source_captured_at: source.captured_at };
    });
    const parameters = profile.parameters.map(parameter => {
      if (parameter.state === "known") {
        if (!Number.isFinite(parameter.value)) throw new Error("Evidence profile numeric value is not finite");
        return `<li><strong>${escape(parameter.id)}: ${escape(parameter.value)} ${escape(parameter.unit)}</strong><p>Conditions: ${escape(parameter.conditions)}. System boundary: ${escape(parameter.system_boundary)}.</p><p>Conversion: ${escape(parameter.conversion_method)}. Supporting claims: ${escape(parameter.claim_ids.join(", "))}.</p><p>Original text: ${escape(parameter.original_text)}</p></li>`;
      }
      if (!missingStates.has(parameter.state) || typeof parameter.reason !== "string" || !parameter.reason.trim()) {
        throw new Error("Evidence profile missing value needs a state and reason");
      }
      return `<li><strong>${escape(parameter.id)}: ${escape(parameter.state.replaceAll("_", " "))}</strong><p>${escape(parameter.reason)}</p><p>Original catalogue text: ${escape(parameter.original_text)}</p></li>`;
    }).join("");
    const audit = profile.review_disposition.historical_audit;
    const download = "data:application/json;charset=utf-8," +
      encodeURIComponent(exportProfile(document, snapshot, row.id)).replaceAll("'", "%27");
    return `<section class="evidence-profile" aria-label="Evidence profile">
      <h3>Evidence profile</h3>
      <p>Read what each source supports, then inspect the original locator. Source support and classification are separate decisions.</p>
      <dl><div><dt>Entity category</dt><dd>${escape(profile.entity_kind.category.replaceAll("-", " "))} — provisional mapping from “${escape(profile.legacy_kind)}”</dd></div>
      <div><dt>Source support</dt><dd>${citations.length} source-inspected statements; partial support</dd></div>
      <div><dt>Classification</dt><dd>Open; no complete entry decision recorded</dd></div>
      <div><dt>Independent entry review</dt><dd>No whole-entry decision recorded in this profile</dd></div>
      <div><dt>Source rights</dt><dd>Catalogue metadata only; original works are not redistributed</dd></div></dl>
      <p>The inherited source inspection does not record its author's identity. It is not a new independent review.</p>
      <details class="profile-questions"><summary>Historical classification questions — recorded ${escape(audit.audit_date)}</summary>
      <p>These are the preserved historical questions, not a fresh finding about the current source collection. Classification review remains open.</p>
      <ul>${profile.review_disposition.classification.questions.map(question => `<li>${escape(question)}</li>`).join("")}</ul></details>
      <details class="profile-parameters"><summary>Parameters and missing values</summary><ul>${parameters}</ul></details>
      <p><a class="profile-download" href="${escape(download)}" download="${escape(row.id)}-evidence-profile.json">Download this evidence profile (JSON)</a></p>
      ${globalThis.AtlasTaxonomyCitations.render(citations)}
    </section>`;
  }

  globalThis.AtlasTaxonomyEvidenceProfiles = Object.freeze({ readProfile, exportProfile, render });
})();
