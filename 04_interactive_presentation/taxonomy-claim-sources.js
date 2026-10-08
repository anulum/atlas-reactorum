// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source statements in taxonomy details
"use strict";

/** Source-preserving renderer for classic-script consumers and Node hosts. */
var AtlasTaxonomyCitations = (() => {
  /** @type {Record<string, string>} */
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  /**
   * Escape source typography without interpreting it as HTML markup.
   * @param {string} value Original source text.
   * @returns {string} Escaped original wording.
   */
  const escape = (value) =>
    String(value).replace(/[&<>"']/g, (character) => entities[character]);

  /**
   * Describe actual source custody without inventing a retained retrieval date.
   * @param {import("./scripts/taxonomy_citations.cjs").ResolvedCitation} citation Validated exported claim.
   * @returns {string} Original retrieval date or explicit retained-copy uncertainty.
   * @throws {Error} A publisher source lacks its required retrieval date.
   */
  function captureText(citation) {
    if (citation.source_capture_method === "retained-source-review")
      return "Retained source copy; original retrieval date unknown.";
    if (citation.source_captured_at === null)
      throw new Error("Publisher citation source must have a retrieval date");
    return `Source copy retrieved: ${citation.source_captured_at.slice(0, 10)}.`;
  }

  /**
   * Render the bounded statements and exact locators from the validated export.
   * Empty citations retain the pending-review message; no entry approval is implied.
   * @param {readonly import("./scripts/taxonomy_citations.cjs").ResolvedCitation[]} citations Resolved claim_citations on one audit record.
   * @returns {string} HTML for insertion into the actual taxonomy detail dialog.
   * @throws {Error} If a source URL, capture method or retrieval date violates the export contract.
   */
  function render(citations) {
    const heading =
      "<h3>Claim citations</h3><p>These source-inspected statements provide partial support. Full review of this entry remains pending.</p>";
    if (citations.length === 0)
      return (
        heading +
        "<p>No claim-level citation has been added for this entry.</p>"
      );
    return (
      heading +
      '<ul class="claim-citations">' +
      citations
        .map((citation) => {
          if (!/^https:\/\/[a-zA-Z0-9.-]+\/[\S]*$/.test(citation.source_url))
            throw new Error("Citation source must use anonymous HTTPS");
          if (
            !["publisher-tls", "retained-source-review"].includes(
              citation.source_capture_method,
            )
          )
            throw new Error(
              "Citation source has an unsupported capture method",
            );
          const capture = captureText(citation);
          const pages = citation.pdf_pages.length
            ? `; printed page(s) ${citation.printed_pages.join(", ")}; PDF page(s) ${citation.pdf_pages.join(", ")} (one-based)`
            : "";
          const url =
            citation.source_url +
            (citation.pdf_pages.length && !citation.source_url.includes("#")
              ? `#page=${citation.pdf_pages[0]}`
              : "");
          return `<li><p>${escape(citation.statement)}</p><p><a href="${escape(url)}" target="_blank" rel="noopener noreferrer">${escape(citation.source_title)}</a> — ${escape(citation.section + pages)}</p><p>${escape(citation.scope)}</p><p>${escape(capture)} Source inspected: ${escape(citation.reviewed_on)}.</p></li>`;
        })
        .join("") +
      "</ul>"
    );
  }

  return Object.freeze({ render });
})();
globalThis.AtlasTaxonomyCitations = AtlasTaxonomyCitations;
