// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — reproducible taxonomy comparisons and share links
"use strict";

/**
 * Original profiles and sources selected from one immutable catalogue snapshot.
 * @typedef {object} AtlasComparisonBundle
 * @property {string} schema_version Versioned comparison schema.
 * @property {string} metadata_license Metadata licence.
 * @property {string} source_rights Original catalogue-only source boundary.
 * @property {{profile_sha256: string, inputs: import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument["inputs"]}} snapshot Complete document and source identities.
 * @property {{entry_ids: string[]}} selection Stable identities in display order.
 * @property {import("./taxonomy-evidence-profile.js").AtlasEvidenceProfile[]} profiles Original selected profiles.
 * @property {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument["sources"]} sources Every supporting original source.
 * @property {{parameter_id: string, state: string, reason: string}[]} parameter_comparisons Declared-context compatibility without numerical merging.
 */

/** Source-preserving comparison facade for classic-script and Node consumers. */
var AtlasTaxonomyComparison = (() => {
  /** @type {Record<string, string>} */
  const escaped = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  /**
   * Escape a displayed original taxonomy cell or compatibility explanation.
   * @param {string|number|null|string[]} value Original source-bound cell.
   * @returns {string} Escaped text retaining the original display semantics.
   */
  const escape = (value) =>
    String(value).replace(/[&<>"']/g, (character) => escaped[character]);
  const hashPattern = /^[a-f0-9]{64}$/;
  const missingStates = new Set([
    "not_reported",
    "not_reviewed",
    "not_applicable",
    "disputed",
  ]);

  /**
   * Require two or three distinct nonempty textual catalogue identities.
   * @param {unknown} ids External ordered selection before validation.
   * @returns {asserts ids is string[]} Checked explicit selection.
   * @throws {Error} The selection is absent, duplicated, malformed or outside its size bound.
   */
  function checkSelection(ids) {
    if (
      !Array.isArray(ids) ||
      ids.length < 2 ||
      ids.length > 3 ||
      ids.some((id) => typeof id !== "string" || !id.trim()) ||
      new Set(ids).size !== ids.length
    ) {
      throw new Error("Choose two or three different catalogue entries");
    }
  }

  /**
   * Identify complete profile content using SHA-256 of its UTF-8 JSON.stringify representation.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument|null} document Complete, deterministically generated profile document.
   * @returns {Promise<string>} Lowercase digest covering all profiles, sources and input hashes.
   * @throws {Error} When the catalogue is incomplete, unsupported or unavailable.
   */
  async function snapshot(document) {
    if (
      !document ||
      !Array.isArray(document.records) ||
      document.records.length === 0
    ) {
      throw new Error("Comparison catalogue is unavailable");
    }
    globalThis.AtlasTaxonomyEvidenceProfiles.readProfile(
      document,
      document.inputs.taxonomy_sha256,
      document.records[0].entry_id,
    );
    const digest = await globalThis.crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(JSON.stringify(document)),
    );
    return Array.from(new Uint8Array(digest), (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("");
  }

  /**
   * Compare only explicitly declared parameter contexts and retain missing values.
   * @param {readonly import("./taxonomy-evidence-profile.js").AtlasEvidenceProfile[]} profiles Original selected profiles.
   * @returns {AtlasComparisonBundle["parameter_comparisons"]} Compatibility descriptions without conversions or averaging.
   * @throws {Error} A numeric value lacks its finite value, context or original supporting claims.
   */
  function parameters(profiles) {
    /** @type {readonly ("unit"|"conditions"|"system_boundary"|"conversion_method")[]} */
    const context = [
      "unit",
      "conditions",
      "system_boundary",
      "conversion_method",
    ];
    const ids = [
      ...new Set(
        profiles.flatMap((profile) =>
          profile.parameters.map((parameter) => parameter.id),
        ),
      ),
    ];
    for (const profile of profiles) {
      for (const parameter of profile.parameters) {
        if (parameter.state === "known") {
          if (
            !Number.isFinite(parameter.value) ||
            context.some(
              (field) =>
                typeof parameter[field] !== "string" ||
                !parameter[field].trim(),
            ) ||
            !Array.isArray(parameter.claim_ids) ||
            parameter.claim_ids.length === 0 ||
            parameter.claim_ids.some(
              (id) => !profile.claims.some((claim) => claim.claim_id === id),
            )
          )
            throw new Error(
              "Comparison parameter needs finite source-bound units and context",
            );
        } else if (
          !missingStates.has(parameter.state) ||
          typeof parameter.reason !== "string" ||
          !parameter.reason.trim()
        ) {
          throw new Error(
            "Comparison missing parameter needs a state and reason",
          );
        }
      }
    }
    return ids.map((id) => {
      const cells = profiles.map((profile) =>
        profile.parameters.find((parameter) => parameter.id === id),
      );
      if (
        cells.some((parameter) => !parameter || parameter.state !== "known")
      ) {
        return {
          parameter_id: id,
          state: "not_comparable",
          reason:
            "At least one entry has no source-bound numeric value. Original text and missing-value reasons are retained.",
        };
      }
      const known =
        /** @type {import("./taxonomy-evidence-profile.js").AtlasKnownParameter[]} */ (
          cells
        );
      const differences = context.filter((field) =>
        known.some((parameter) => parameter[field] !== known[0][field]),
      );
      return {
        parameter_id: id,
        state: differences.length ? "not_comparable" : "same_declared_context",
        reason: differences.length
          ? `Declared context differs: ${differences.join(", ")}. No numerical conversion or merging is performed.`
          : "Values share their declared unit, conditions, system boundary and conversion method. This is metadata compatibility, not scientific acceptance; no numerical merging is performed.",
      };
    });
  }

  /**
   * Export an ordered comparison with original claims, sources, input hashes and rights.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} document Complete profile document from the current static snapshot.
   * @param {string} expectedSnapshot Explicit complete-profile digest, never a latest-data alias.
   * @param {unknown} entryIds External ordered identities, checked before use.
   * @returns {Promise<AtlasComparisonBundle>} Versioned catalogue-only bundle; no guessed values or source bodies.
   * @throws {Error} On stale content, unsupported review states or invalid selections.
   */
  async function createComparison(document, expectedSnapshot, entryIds) {
    checkSelection(entryIds);
    const content = structuredClone(document);
    if (
      !hashPattern.test(expectedSnapshot) ||
      (await snapshot(content)) !== expectedSnapshot
    ) {
      throw new Error(
        "The linked comparison snapshot is unavailable; current data were not substituted",
      );
    }
    const selected = entryIds.map(
      (id) =>
        /** @type {import("./taxonomy-evidence-profile.js").AtlasEntryEvidenceExport} */ (
          JSON.parse(
            globalThis.AtlasTaxonomyEvidenceProfiles.exportProfile(
              content,
              content.inputs.taxonomy_sha256,
              id,
            ),
          )
        ),
    );
    const profiles = selected.map((entry) => entry.profile);
    const used = new Set(
      selected.flatMap((entry) => entry.sources.map((source) => source.id)),
    );
    return {
      schema_version: "atlas-comparison-1.0.0",
      metadata_license: "AGPL-3.0-or-later",
      source_rights: "catalogue-only; original not redistributed",
      snapshot: { profile_sha256: expectedSnapshot, inputs: content.inputs },
      selection: { entry_ids: [...entryIds] },
      profiles,
      sources: content.sources.filter((source) => used.has(source.id)),
      parameter_comparisons: parameters(profiles),
    };
  }

  /**
   * Encode version, complete-profile digest and ordered stable IDs in the page fragment.
   * @param {string} pageUrl Current static presentation URL, including its document path.
   * @param {string} expectedSnapshot Explicit lowercase SHA-256 of complete profile content.
   * @param {unknown} entryIds External ordered identities, checked before link construction.
   * @returns {string} Absolute reproducible link; unrelated page query fields are preserved.
   * @throws {Error} On malformed identity, snapshot or unsupported URL protocol/credentials.
   */
  function shareUrl(pageUrl, expectedSnapshot, entryIds) {
    checkSelection(entryIds);
    if (!hashPattern.test(expectedSnapshot))
      throw new Error("Comparison snapshot hash is invalid");
    const url = new URL(pageUrl);
    if (
      !["https:", "http:", "file:"].includes(url.protocol) ||
      url.username ||
      url.password
    ) {
      throw new Error("Comparison page URL is unsupported");
    }
    const query = new URLSearchParams({
      version: "1",
      snapshot: expectedSnapshot,
    });
    entryIds.forEach((id) => query.append("entry", id));
    url.hash = "compare?" + query.toString();
    return url.href;
  }

  /**
   * Read a shared comparison without silently replacing malformed or older snapshots.
   * @param {string} pageUrl Absolute page URL supplied by browser navigation.
   * @returns {{snapshot: string, entryIds: string[]}|null} Ordered explicit selection, or null for an ordinary page anchor.
   * @throws {Error} On unsupported, duplicated, missing or unknown comparison fields.
   */
  function readUrl(pageUrl) {
    const hash = new URL(pageUrl).hash;
    if (!hash.startsWith("#compare?")) return null;
    const query = new URLSearchParams(hash.slice("#compare?".length));
    const selectedSnapshot = query.get("snapshot");
    if (
      query.getAll("version").length !== 1 ||
      query.get("version") !== "1" ||
      query.getAll("snapshot").length !== 1 ||
      selectedSnapshot === null ||
      !hashPattern.test(selectedSnapshot) ||
      [...query.keys()].some(
        (key) => !["version", "snapshot", "entry"].includes(key),
      )
    ) {
      throw new Error("Shared comparison format is unavailable or invalid");
    }
    const entryIds = query.getAll("entry");
    checkSelection(entryIds);
    return { snapshot: selectedSnapshot, entryIds };
  }

  /**
   * Render the validated comparison, original contexts and accessible source disclosures.
   * @param {import("./taxonomy-evidence-profile.js").AtlasEvidenceDocument} document Complete source-bound evidence profile document.
   * @param {string} expectedSnapshot Explicit complete-profile digest.
   * @param {string[]} entryIds Two or three distinct ordered catalogue identities.
   * @returns {Promise<{bundle: AtlasComparisonBundle, html: string}>} Escaped HTML and the identical downloadable comparison bundle.
   */
  async function renderComparison(document, expectedSnapshot, entryIds) {
    const bundle = await createComparison(document, expectedSnapshot, entryIds);
    const profiles = bundle.profiles;
    /**
     * Render one original catalogue dimension in the existing selection order.
     * @param {string} label Accessible dimension name.
     * @param {keyof import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow} field Original row field.
     * @returns {string} Escaped comparison table row.
     */
    const line = (label, field) =>
      `<tr><th scope="row">${escape(label)}</th>${profiles
        .map((profile) => `<td>${escape(profile.taxonomy_record[field])}</td>`)
        .join("")}</tr>`;
    const parameterRows = bundle.parameter_comparisons
      .map(
        (comparison) =>
          `<tr><th scope="row">${escape(comparison.parameter_id)}</th>${profiles
            .map((profile) => {
              const parameter = profile.parameters.find(
                (parameter) => parameter.id === comparison.parameter_id,
              );
              const value = !parameter
                ? "No parameter metadata in this profile"
                : parameter.state === "known"
                  ? `${parameter.value} ${parameter.unit}; conditions: ${parameter.conditions}; system boundary: ${parameter.system_boundary}; conversion: ${parameter.conversion_method}; original text: ${parameter.original_text}`
                  : `${parameter.state.replaceAll("_", " ")}: ${parameter.reason} Original text: ${parameter.original_text}`;
              return `<td>${escape(value)}</td>`;
            })
            .join("")}</tr>`,
      )
      .join("");
    const sources = new Map(
      bundle.sources.map((source) => [source.id, source]),
    );
    const disclosures = profiles
      .map((profile) => {
        const citations = profile.claims.map((claim) => {
          const source =
            /** @type {import("./scripts/taxonomy_citations.cjs").CitationSource} */ (
              sources.get(claim.citation.source_id)
            );
          return {
            ...claim.citation,
            source_title: source.title,
            source_url: source.url,
            source_sha256: source.sha256,
            source_capture_method: source.capture_method,
            source_captured_at: source.captured_at,
          };
        });
        return `<details class="comparison-sources"><summary>Sources for ${escape(profile.taxonomy_record.name)}</summary>${globalThis.AtlasTaxonomyCitations.render(citations)}</details>`;
      })
      .join("");
    const html = `<p>Legacy classification labels remain open to review. Source support is partial; this comparison does not establish complete entry acceptance.</p>
      <table class="comparison"><caption>Original catalogue descriptions for the selected systems</caption><thead><tr><th scope="col">Dimension</th>${profiles.map((profile) => `<th scope="col">${escape(profile.taxonomy_record.name)}</th>`).join("")}</tr></thead><tbody>
      ${line("Domain", "domain")}${line("Family", "family")}${line("Principle", "principle")}${line("Legacy maturity", "maturity")}${line("Legacy evidence", "evidence")}${line("Evidence scope", "evidence_scope")}${line("Strength", "strength")}${line("Critical challenge", "challenge")}${line("Original temperature text", "temp")}${line("Mode", "mode")}${parameterRows}</tbody></table>
      <ul class="comparison-context">${bundle.parameter_comparisons.map((comparison) => `<li><strong>${escape(comparison.parameter_id)}: ${escape(comparison.state.replaceAll("_", " "))}</strong> ${escape(comparison.reason)}</li>`).join("")}</ul>${disclosures}`;
    return { bundle, html };
  }

  return Object.freeze({
    snapshot,
    createComparison,
    shareUrl,
    readUrl,
    renderComparison,
  });
})();
globalThis.AtlasTaxonomyComparison = AtlasTaxonomyComparison;
