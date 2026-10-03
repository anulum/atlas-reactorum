// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — immutable profile snapshots and source-linked revisions
"use strict";

(() => {
  const version = "atlas-evidence-history-1.0.0";
  const hashPattern = /^[a-f0-9]{64}$/;

  /**
   * Hash a complete JSON value using the existing UTF-8 snapshot representation.
   * @param {object} value Source metadata or history with original member order.
   * @returns {Promise<string>} Lowercase SHA-256; integrity does not establish authorship.
   */
  async function digest(value) {
    const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(value)));
    return Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, "0")).join("");
  }

  /**
   * Require a canonical UTC journal observation, separate from source dates.
   * @param {string} value Explicit UTC timestamp supplied by the journal observer.
   * @returns {string} Unchanged timestamp with millisecond precision.
   * @throws {Error} On missing, impossible or noncanonical dates.
   */
  function observation(value) {
    if (typeof value !== "string" || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value) ||
        !Number.isFinite(Date.parse(value)) || new Date(value).toISOString() !== value) {
      throw new Error("History observation needs a valid explicit UTC timestamp");
    }
    return value;
  }

  function checkDocument(document) {
    if (!document || !Array.isArray(document.sources) ||
        new Set(document.sources.map(source => source.id)).size !== document.sources.length) {
      throw new Error("History source registry is unavailable or duplicated");
    }
    const ids = new Set();
    for (const profile of document.records) {
      globalThis.AtlasTaxonomyEvidenceProfiles.render(document, document.inputs.taxonomy_sha256, profile.taxonomy_record);
      for (const claim of profile.claims) {
        if (ids.has(claim.claim_id)) throw new Error("History claim identity is duplicated");
        ids.add(claim.claim_id);
      }
    }
  }

  /**
   * Validate every retained snapshot and its ordered observation references.
   * @param {object} history Complete retained journal; no snapshot may be pruned.
   * @returns {Promise<void>} Resolves after complete original-source integrity checks.
   * @throws {Error} On unsupported format, altered snapshots or broken chronology.
   */
  async function validate(history) {
    if (!history || history.schema_version !== version ||
        history.metadata_license !== "AGPL-3.0-or-later" ||
        history.source_rights !== "catalogue-only; original not redistributed" ||
        !Array.isArray(history.snapshots) || !history.snapshots.length ||
        !Array.isArray(history.imports) || !history.imports.length) {
      throw new Error("Evidence history format is unavailable");
    }
    const snapshots = new Set();
    for (const snapshot of history.snapshots) {
      if (!hashPattern.test(snapshot.profile_sha256) || snapshots.has(snapshot.profile_sha256) ||
          await digest(snapshot.document) !== snapshot.profile_sha256) {
        throw new Error("History snapshot is altered or duplicated");
      }
      await globalThis.AtlasTaxonomyComparison.snapshot(snapshot.document);
      checkDocument(snapshot.document);
      snapshots.add(snapshot.profile_sha256);
    }
    let previousTime = "";
    let previousHash = "";
    const observed = new Set();
    for (const entry of history.imports) {
      const time = observation(entry.observed_at);
      if (time <= previousTime || entry.profile_sha256 === previousHash || !snapshots.has(entry.profile_sha256)) {
        throw new Error("History observations are reversed, repeated or unbound");
      }
      previousTime = time;
      previousHash = entry.profile_sha256;
      observed.add(entry.profile_sha256);
    }
    if (observed.size !== snapshots.size) throw new Error("History contains an unobserved snapshot");
  }

  /**
   * Import a validated whole catalogue without replacing previous source content.
   * @param {object|null} history Existing journal, or null for an explicit first observation.
   * @param {object} document Complete real source-bound profile catalogue.
   * @param {string} observedAt Actual observer timestamp, never a reconstructed source date.
   * @returns {Promise<object>} New immutable-content journal; identical latest imports are idempotent.
   * @throws {Error} When sources, chronology or existing history fail validation.
   */
  async function importProfiles(history, document, observedAt) {
    const prior = structuredClone(history);
    const content = structuredClone(document);
    observation(observedAt);
    const profileHash = await globalThis.AtlasTaxonomyComparison.snapshot(content);
    checkDocument(content);
    const result = prior === null ? { schema_version: version, metadata_license: "AGPL-3.0-or-later",
      source_rights: "catalogue-only; original not redistributed", snapshots: [], imports: [] } : prior;
    if (prior !== null) {
      await validate(prior);
      const latest = prior.imports.at(-1);
      if (latest.profile_sha256 === profileHash) return prior;
      if (observedAt <= latest.observed_at) throw new Error("New history observation must follow its predecessor");
    }
    if (!result.snapshots.some(snapshot => snapshot.profile_sha256 === profileHash)) {
      result.snapshots.push({ profile_sha256: profileHash, document: content });
    }
    result.imports.push({ profile_sha256: profileHash, observed_at: observedAt });
    return result;
  }

  /**
   * Read one claim's actual revisions, including removals and subsequent returns.
   * @param {object} history Whole journal with retained original snapshots.
   * @param {string} expectedDigest Explicit hash of the complete journal content.
   * @param {string} entryId Stable profile identity; names never merge identities.
   * @param {string} claimId Stable original claim identity within that profile.
   * @returns {Promise<object>} Revisions with original claims, sources, dates and rights.
   * @throws {Error} On stale history, missing identities or unsupported retained content.
   */
  async function readClaim(history, expectedDigest, entryId, claimId) {
    const content = structuredClone(history);
    await validate(content);
    if (!hashPattern.test(expectedDigest) || await digest(content) !== expectedDigest) {
      throw new Error("The linked evidence history is unavailable; current content was not substituted");
    }
    const snapshots = new Map(content.snapshots.map(snapshot => [snapshot.profile_sha256, snapshot.document]));
    const revisions = [];
    let lastSignature;
    for (const imported of content.imports) {
      const document = snapshots.get(imported.profile_sha256);
      const profile = document.records.find(record => record.entry_id === entryId);
      const claim = profile ? profile.claims.find(record => record.claim_id === claimId) : undefined;
      const source = claim ? document.sources.find(record => record.id === claim.citation.source_id) : null;
      const original = { claim: claim || null, source };
      const signature = JSON.stringify(original);
      if (signature === lastSignature) continue;
      const previous = revisions.at(-1);
      const changes = [];
      if (!previous) changes.push("first-journal-observation");
      else {
        if (JSON.stringify(previous.claim) !== JSON.stringify(original.claim)) changes.push("claim-or-locator");
        if (JSON.stringify(previous.source) !== JSON.stringify(source)) changes.push("source-metadata");
      }
      const revision = { profile_sha256: imported.profile_sha256,
        state: claim ? "present" : "not-in-snapshot", ...original, changes,
        dates: { atlas_observed_at: imported.observed_at, source_acquired_at: source ? source.captured_at : null,
          claim_reviewed_on: claim ? claim.citation.reviewed_on : null,
          source_event_on: null, source_published_on: null } };
      revisions.push({ revision_sha256: await digest(revision), ...revision });
      lastSignature = signature;
    }
    if (!revisions.some(revision => revision.claim !== null)) throw new Error("History claim identity is unavailable");
    return { schema_version: "atlas-claim-history-1.0.0", metadata_license: content.metadata_license,
      source_rights: content.source_rights, history_sha256: expectedDigest,
      entry_id: entryId, claim_id: claimId, revisions };
  }

  globalThis.AtlasEvidenceHistory = Object.freeze({ digest, observation, validate, importProfiles, readClaim });
})();
