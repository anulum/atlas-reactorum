// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — primary research decisions in map details
"use strict";

/**
 * Original primary-source decision; every ledger column remains textual.
 * @typedef {object} ResearchPrimaryDecision
 * @property {string} stable_id Original facility identity.
 * @property {string} field Operator, purpose or first-criticality field.
 * @property {string} value Selected or held original wording, or explicit absence.
 * @property {string} selection Producer's individual disposition.
 * @property {string} source_id Original supporting source identity, or absence.
 * @property {string} source_title Original source title.
 * @property {string} source_url Anonymous HTTPS locator.
 * @property {string} source_sha256 Original source digest.
 * @property {string} source_class Native source or explicitly held discovery lead.
 * @property {string} source_document_date Publisher date with original precision.
 * @property {string} source_capture_date Retrieval date, distinct from event and publication.
 * @property {string} locator Exact source location.
 * @property {string} scope Original support boundary.
 * @property {string} rights Source-specific rights, never inferred from capture.
 * @property {string} date_precision Original event precision, or absence.
 * @property {string} assertion_basis Recorded decision basis.
 * @property {string} related_evidence Original JSON citation cell, or absence.
 */

/**
 * Related citation retaining alternate values without promoting their admissibility.
 * @typedef {object} RelatedResearchCitation
 * @property {string} source_id Original related-source identity.
 * @property {string} original_url Anonymous HTTPS source locator.
 * @property {string} sha256 Original source digest.
 * @property {string} [locator] Optional source location.
 * @property {string} [admissibility] Optional original support scope.
 * @property {string} [reported_value] Optional alternate reported value.
 */

/** Primary decision renderer shared by browser and native consumers. */
var PrimaryResearchAssertions = (() => {
  const keys = [
    "stable_id",
    "field",
    "value",
    "selection",
    "source_id",
    "source_title",
    "source_url",
    "source_sha256",
    "source_class",
    "source_document_date",
    "source_capture_date",
    "locator",
    "scope",
    "rights",
    "date_precision",
    "assertion_basis",
    "related_evidence",
  ];
  /** @type {Record<string, string>} */
  const fields = {
    operator: "Operator",
    purpose: "Purpose",
    first_criticality: "First criticality",
  };
  /** @type {Record<string, string>} */
  const decisions = {
    selected: "Selected value",
    held: "Unresolved claim",
    unknown: "Unknown",
    not_applicable: "Not applicable",
    never_critical: "Never critical",
    planned: "Planned",
    composite: "Composite identity",
  };
  const native = [
    "native_original_pdf",
    "native_original_html",
    "native_original_facsimile",
  ];
  /** @type {Record<string, string>} */
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  const refusal =
    '<p role="status">Primary research decisions are unavailable.</p>';

  /**
   * Escape publisher wording for text and quoted HTML attributes.
   * @param {string} value Original publisher or reviewer wording.
   * @returns {string} Text safe for both HTML destinations.
   */
  function escape(value) {
    return value.replace(/[&<>"']/g, (character) => entities[character]);
  }

  /**
   * Refuse the original C0 control range while preserving publisher typography.
   * @param {string} value Original source text after scalar type checking.
   * @returns {boolean} Whether U+0000 through U+001F occurs in the text.
   */
  function containsControl(value) {
    return Array.from(value).some((character) => character.charCodeAt(0) <= 31);
  }

  /**
   * Check an anonymous HTTPS citation without displaying parser diagnostics.
   * @param {string} value Original source URL.
   * @returns {boolean} Whether the link preserves anonymous HTTPS custody.
   */
  function sourceLink(value) {
    if (!/^https:\/\/[^/\s\\][^\s\\]*$/.test(value)) return false;
    try {
      const url = new URL(value);
      return (
        !!url.hostname && !url.username && !url.password && url.port !== "0"
      );
    } catch {
      return false;
    }
  }

  /**
   * Retain year/month/day precision while rejecting impossible calendar dates.
   * @param {string} value Original date or an explicitly absent date.
   * @returns {boolean} Whether the supplied calendar and precision are valid.
   */
  function date(value) {
    if (!value) return true;
    if (!/^\d{4}(?:-\d{2}(?:-\d{2})?)?$/.test(value)) return false;
    const [year, month = 1, day = 1] = value.split("-").map(Number);
    const actual = new Date(0);
    actual.setUTCFullYear(year, month - 1, day);
    return (
      year > 0 &&
      actual.getUTCFullYear() === year &&
      actual.getUTCMonth() === month - 1 &&
      actual.getUTCDate() === day
    );
  }

  /**
   * Parse retained related citations without accepting unknown columns or unsafe links.
   * @param {string} value Ledger JSON cell; an empty cell supplies no citations.
   * @returns {RelatedResearchCitation[]|null} Original citations or a refused input.
   */
  function related(value) {
    if (!value) return [];
    try {
      /** @type {unknown} */
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) return null;
      const rows = /** @type {unknown[]} */ (parsed);
      const allowed = [
        "source_id",
        "original_url",
        "sha256",
        "locator",
        "admissibility",
        "reported_value",
      ];
      if (
        rows.some((row) => {
          if (!row || typeof row !== "object") return true;
          const original = /** @type {Record<string, unknown>} */ (row);
          if (
            Object.entries(original).some(
              ([key, text]) =>
                !allowed.includes(key) ||
                typeof text !== "string" ||
                containsControl(text),
            )
          )
            return true;
          const cells = /** @type {Record<string, string|undefined>} */ (
            original
          );
          return (
            !cells.source_id?.trim() ||
            !sourceLink(cells.original_url || "") ||
            !/^[a-f0-9]{64}$/.test(cells.sha256 || "")
          );
        })
      )
        return null;
      return /** @type {RelatedResearchCitation[]} */ (rows);
    } catch {
      return null;
    }
  }

  /**
   * Reject a decision which cannot preserve the producer's scientific contract.
   * @param {unknown} row Original serialized assertion before validation.
   * @returns {row is ResearchPrimaryDecision} Whether every source, disposition and event contract holds.
   */
  function valid(row) {
    if (
      !row ||
      typeof row !== "object" ||
      Object.keys(row).length !== keys.length
    )
      return false;
    const cells = /** @type {Record<string, unknown>} */ (row);
    if (
      keys.some((key) => {
        const value = cells[key];
        return typeof value !== "string" || containsControl(value);
      })
    )
      return false;
    const decision = /** @type {ResearchPrimaryDecision} */ (row);
    if (
      !decision.stable_id.trim() ||
      !Object.hasOwn(fields, decision.field) ||
      !Object.hasOwn(decisions, decision.selection) ||
      !decision.scope.trim() ||
      !decision.assertion_basis.trim()
    )
      return false;
    /** @type {readonly (keyof ResearchPrimaryDecision)[]} */
    const sourceKeys = [
      "source_title",
      "source_url",
      "source_sha256",
      "source_class",
      "locator",
      "rights",
    ];
    if (decision.source_id) {
      if (
        sourceKeys.some((key) => !decision[key].trim()) ||
        !sourceLink(decision.source_url) ||
        !/^[a-f0-9]{64}$/.test(decision.source_sha256) ||
        ![
          ...native,
          "tool_rendered_author_page_lead",
          "native_discovery_registry_json",
        ].includes(decision.source_class)
      )
        return false;
    } else if (sourceKeys.some((key) => decision[key])) return false;
    if (
      decision.selection === "selected" &&
      (!decision.value.trim() ||
        !decision.source_id ||
        !native.includes(decision.source_class))
    )
      return false;
    if (!["selected", "held"].includes(decision.selection) && decision.value)
      return false;
    if (decision.selection === "held" && decision.value && !decision.source_id)
      return false;
    if (
      !date(decision.source_document_date) ||
      !date(decision.source_capture_date) ||
      related(decision.related_evidence) === null
    )
      return false;
    if (decision.field === "first_criticality" && decision.value) {
      /** @type {Record<number, string>} */
      const precision = { 4: "year", 7: "month", 10: "day" };
      return (
        date(decision.value) &&
        decision.date_precision === precision[decision.value.length] &&
        !(
          decision.selection === "selected" &&
          decision.source_capture_date.length === 10 &&
          decision.value > decision.source_capture_date
        )
      );
    }
    return !decision.date_precision;
  }

  /**
   * Render every reviewed disposition, keeping held values separate from selected cells.
   * @param {unknown} assertions Original ledger rows attached to one map facility.
   * @returns {string} Escaped detail HTML, an empty section or a safe refusal.
   */
  function render(assertions) {
    if (!Array.isArray(assertions)) return refusal;
    if (!assertions.length) return "";
    const candidates = /** @type {unknown[]} */ (assertions);
    if (candidates.some((row) => !valid(row))) return refusal;
    const checked = /** @type {ResearchPrimaryDecision[]} */ (candidates);
    if (
      new Set(checked.map((row) => `${row.stable_id}:${row.field}`)).size !==
        checked.length ||
      new Set(checked.map((row) => row.stable_id)).size !== 1
    )
      return refusal;
    return (
      '<section class="field-sources primary-research-sources"><h3>Primary research decisions</h3><p>Held claims do not fill the reactor record. Event precision, document dates and retrieval dates describe different things.</p>' +
      checked
        .map(
          (row) =>
            `<details><summary>${escape(fields[row.field])}: ${escape(decisions[row.selection])}${row.value ? ` · ${escape(row.value)}` : ""}</summary><p>${escape(row.scope)}</p><p>${escape(row.assertion_basis)}</p>${row.date_precision ? `<p>Event precision: ${escape(row.date_precision)}</p>` : ""}${row.source_id ? `<p>${escape(row.source_title)} · document ${escape(row.source_document_date || "date unknown")} · retrieved ${escape(row.source_capture_date || "date unknown")}</p><p>Location in source: ${escape(row.locator)}</p><p>Rights: ${escape(row.rights)}</p><p>Original source SHA-256: ${escape(row.source_sha256)}</p><a href="${escape(row.source_url)}" target="_blank" rel="noopener">Original source ↗</a>` : "<p>No admissible original source supplies this field.</p>"}${/** @type {RelatedResearchCitation[]} */ (related(row.related_evidence)).map((citation) => `<p>Related evidence: ${escape(citation.source_id)} · ${escape(citation.locator || "location not supplied")} · ${escape(citation.admissibility || "scope not supplied")}${citation.reported_value ? ` · reported ${escape(citation.reported_value)}` : ""} · SHA-256 ${escape(citation.sha256)} <a href="${escape(citation.original_url)}" target="_blank" rel="noopener">Source ↗</a></p>`).join("")}</details>`,
        )
        .join("") +
      "</section>"
    );
  }

  return Object.freeze({ render });
})();

globalThis.PrimaryResearchAssertions = PrimaryResearchAssertions;
if (typeof module !== "undefined") module.exports = PrimaryResearchAssertions;
