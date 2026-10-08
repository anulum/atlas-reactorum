// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original claim revisions and exact historical links
"use strict";

/**
 * Explicit selection encoded by a versioned history link.
 * @typedef {object} AtlasHistorySelection
 * @property {string} historyHash Exact whole-journal digest.
 * @property {string} entryId Stable selected entry.
 * @property {string} claimId Stable selected claim.
 * @property {string} revisionHash Exact dated revision digest.
 */

/** Source-preserving history presentation facade for browser and native consumers. */
var AtlasEvidenceHistoryRender = (() => {
  /** @type {Record<string, string>} */
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  /**
   * Escape original wording, dates and retained JSON for display without markup interpretation.
   * @param {string} value Original text destined for HTML text or quoted attributes.
   * @returns {string} Escaped unchanged wording.
   */
  const escape = (value) =>
    String(value).replace(/[&<>"']/g, (character) => entities[character]);
  const hashPattern = /^[a-f0-9]{64}$/;

  /**
   * Require explicit complete history/revision hashes and nonempty stable identities.
   * @param {string|null} historyHash Complete journal hash from the link parser.
   * @param {string|null} entryId Selected stable entry.
   * @param {string|null} claimId Selected stable claim.
   * @param {string|null} revisionHash Explicit dated revision.
   * @returns {AtlasHistorySelection} Checked link state without a latest-content fallback.
   * @throws {Error} A hash or identity is missing or malformed.
   */
  function checkSelection(historyHash, entryId, claimId, revisionHash) {
    if (
      !hashPattern.test(historyHash || "") ||
      !hashPattern.test(revisionHash || "") ||
      typeof entryId !== "string" ||
      !entryId ||
      typeof claimId !== "string" ||
      !claimId
    ) {
      throw new Error("Historical link identities are unavailable");
    }
    return {
      historyHash: /** @type {string} */ (historyHash),
      entryId,
      claimId,
      revisionHash: /** @type {string} */ (revisionHash),
    };
  }

  /**
   * Render retained original wording, source metadata and distinct date meanings.
   * @param {import("./evidence-history.js").AtlasEvidenceJournal} history Complete journal containing all prior source snapshots.
   * @param {string} historyHash Expected complete journal digest.
   * @param {string} entryId Stable entry identity, including retired entries.
   * @param {string} claimId Stable original claim identity.
   * @param {string|null} revisionHash Exact dated revision, or null for the last observation.
   * @returns {Promise<{bundle: import("./evidence-history.js").AtlasClaimHistory, selected: import("./evidence-history.js").AtlasClaimRevision, html: string}>} Escaped full timeline, original bundle and selected revision.
   * @throws {Error} On unavailable history, identities or dated revision.
   */
  async function render(
    history,
    historyHash,
    entryId,
    claimId,
    revisionHash = null,
  ) {
    const bundle = await globalThis.AtlasEvidenceHistory.readClaim(
      history,
      historyHash,
      entryId,
      claimId,
    );
    const selected =
      revisionHash === null
        ? bundle.revisions.at(-1)
        : bundle.revisions.find(
            (revision) => revision.revision_sha256 === revisionHash,
          );
    if (!selected) throw new Error("The linked dated revision is unavailable");
    const timeline = bundle.revisions
      .map((revision) => {
        const dates = Object.entries(revision.dates)
          .map(
            ([meaning, value]) =>
              "<div><dt>" +
              escape(meaning.replaceAll("_", " ")) +
              "</dt><dd>" +
              escape(value === null ? "Unknown / not recorded" : value) +
              "</dd></div>",
          )
          .join("");
        let original =
          "<p>This claim was not present in this imported snapshot. Earlier source content remains in this timeline.</p>";
        if (revision.state === "present") {
          const citation = revision.claim.citation;
          original =
            "<p class='history-statement'>" +
            escape(revision.claim.original_statement) +
            "</p>" +
            "<p><strong>Locator:</strong> " +
            escape(citation.section) +
            "; PDF pages " +
            escape(citation.pdf_pages.join(", ")) +
            "; printed pages " +
            escape(citation.printed_pages.join(", ")) +
            "</p><p><strong>Support boundary:</strong> " +
            escape(citation.scope) +
            "</p>" +
            "<p><a href='" +
            escape(revision.source.url) +
            "' target='_blank' rel='noopener noreferrer'>" +
            escape(revision.source.title) +
            "</a></p><p><strong>Source capture:</strong> " +
            escape(revision.source.capture_method) +
            " · SHA-256 <code>" +
            escape(revision.source.sha256) +
            "</code></p>";
        }
        return (
          "<li class='history-revision" +
          (revision === selected ? " history-selected" : "") +
          "'><h4>" +
          escape(revision.dates.atlas_observed_at) +
          " · " +
          escape(revision.state) +
          "</h4><p><strong>Recorded change:</strong> " +
          escape(revision.changes.join(", ")) +
          "</p>" +
          original +
          "<dl class='history-dates'>" +
          dates +
          "</dl><details><summary>Inspect the complete original revision</summary>" +
          "<pre>" +
          escape(JSON.stringify(revision, null, 2)) +
          "</pre></details></li>"
        );
      })
      .join("");
    return {
      bundle,
      selected,
      html:
        "<h3>" +
        escape(entryId) +
        " · " +
        escape(claimId) +
        "</h3>" +
        "<p>The journal begins with Atlas's first recorded observation. It does not reconstruct earlier history. " +
        "Source acquisition, claim review, publication and event dates have separate meanings. " +
        "A retained observation does not establish complete entry review or source authorship.</p>" +
        "<ol class='history-timeline'>" +
        timeline +
        "</ol>",
    };
  }

  /**
   * Link to one exact dated revision within an exact complete journal.
   * @param {string} pageUrl Anonymous absolute http, https or file presentation URL.
   * @param {string} historyHash Complete journal digest, never an implicit latest alias.
   * @param {string} entryId Stable profile identity.
   * @param {string} claimId Stable original claim identity.
   * @param {string} revisionHash Dated revision digest, including absence/return observations.
   * @returns {string} Versioned fragment link preserving the page and query.
   * @throws {Error} On missing identities, invalid digests or unsupported page URL.
   */
  function shareUrl(pageUrl, historyHash, entryId, claimId, revisionHash) {
    checkSelection(historyHash, entryId, claimId, revisionHash);
    const url = new URL(pageUrl);
    if (
      !["http:", "https:", "file:"].includes(url.protocol) ||
      url.username ||
      url.password
    ) {
      throw new Error("Historical presentation URL is unsupported");
    }
    url.hash =
      "history?" +
      new URLSearchParams({
        version: "1",
        history: historyHash,
        entry: entryId,
        claim: claimId,
        revision: revisionHash,
      }).toString();
    return url.href;
  }

  /**
   * Parse only exact historical links and refuse ambiguous linked versions.
   * @param {string} pageUrl Absolute current presentation URL.
   * @returns {AtlasHistorySelection|null} Explicit identities/digests, or null for ordinary navigation.
   * @throws {Error} On unknown, duplicated, unsupported or missing linked fields.
   */
  function readUrl(pageUrl) {
    const hash = new URL(pageUrl).hash;
    if (!hash.startsWith("#history?")) return null;
    const query = new URLSearchParams(hash.slice(9));
    const fields = ["version", "history", "entry", "claim", "revision"];
    if (
      fields.some((field) => query.getAll(field).length !== 1) ||
      query.get("version") !== "1" ||
      [...query.keys()].some((field) => !fields.includes(field))
    ) {
      throw new Error("Shared history format is unavailable or invalid");
    }
    const state = {
      historyHash: query.get("history"),
      entryId: query.get("entry"),
      claimId: query.get("claim"),
      revisionHash: query.get("revision"),
    };
    return checkSelection(
      state.historyHash,
      state.entryId,
      state.claimId,
      state.revisionHash,
    );
  }

  return Object.freeze({ render, shareUrl, readUrl });
})();
globalThis.AtlasEvidenceHistoryRender = AtlasEvidenceHistoryRender;
