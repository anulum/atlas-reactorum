// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — primary research decisions in map details
"use strict";

(() => {
  const keys = ["stable_id", "field", "value", "selection", "source_id", "source_title", "source_url", "source_sha256", "source_class", "source_document_date", "source_capture_date", "locator", "scope", "rights", "date_precision", "assertion_basis", "related_evidence"];
  const fields = {operator: "Operator", purpose: "Purpose", first_criticality: "First criticality"};
  const decisions = {selected: "Selected value", held: "Unresolved claim", unknown: "Unknown", not_applicable: "Not applicable", never_critical: "Never critical", planned: "Planned", composite: "Composite identity"};
  const native = ["native_original_pdf", "native_original_html", "native_original_facsimile"];
  const entities = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"};
  const refusal = '<p role="status">Primary research decisions are unavailable.</p>';

  /** Escape publisher wording for text and quoted HTML attributes.
   * @param {string} value Original publisher or reviewer wording.
   * @returns {string} Text safe for both HTML destinations.
   */
  function escape(value) {
    return value.replace(/[&<>"']/g, character => entities[character]);
  }

  /** Check an anonymous HTTPS citation without displaying parser diagnostics.
   * @param {string} value Original source URL.
   * @returns {boolean} Whether the link preserves anonymous HTTPS custody.
   */
  function sourceLink(value) {
    if (!/^https:\/\/[^/\s\\][^\s\\]*$/.test(value)) return false;
    try {
      const url = new URL(value);
      return !!url.hostname && !url.username && !url.password && url.port !== "0";
    } catch {
      return false;
    }
  }

  /** Retain year/month/day precision while rejecting impossible calendar dates.
   * @param {string} value Original date or an explicitly absent date.
   * @returns {boolean} Whether the supplied calendar and precision are valid.
   */
  function date(value) {
    if (!value) return true;
    if (!/^\d{4}(?:-\d{2}(?:-\d{2})?)?$/.test(value)) return false;
    const [year, month = 1, day = 1] = value.split("-").map(Number);
    const actual = new Date(0);
    actual.setUTCFullYear(year, month - 1, day);
    return year > 0 && actual.getUTCFullYear() === year && actual.getUTCMonth() === month - 1 && actual.getUTCDate() === day;
  }

  /** Parse retained related citations without accepting unknown columns or unsafe links.
   * @param {string} value Ledger JSON cell; an empty cell supplies no citations.
   * @returns {Array<Record<string, string>>|null} Original citations or a refused input.
   */
  function related(value) {
    if (!value) return [];
    try {
      const rows = JSON.parse(value);
      const allowed = ["source_id", "original_url", "sha256", "locator", "admissibility", "reported_value"];
      if (!Array.isArray(rows) || rows.some(row => !row || typeof row !== "object" ||
        Object.entries(row).some(([key, text]) => !allowed.includes(key) || typeof text !== "string" || /[\x00-\x1f]/.test(text)) ||
        !row.source_id?.trim() || !sourceLink(row.original_url || "") || !/^[a-f0-9]{64}$/.test(row.sha256))) return null;
      return rows;
    } catch {
      return null;
    }
  }

  /** Reject a decision which cannot preserve the producer's scientific contract.
   * @param {unknown} row Original serialized assertion before validation.
   * @returns {boolean} Whether every source, disposition and event contract holds.
   */
  function valid(row) {
    if (!row || typeof row !== "object" || Object.keys(row).length !== keys.length ||
      keys.some(key => typeof row[key] !== "string" || /[\x00-\x1f]/.test(row[key])) ||
      !row.stable_id.trim() || !Object.hasOwn(fields, row.field) || !Object.hasOwn(decisions, row.selection) ||
      !row.scope.trim() || !row.assertion_basis.trim()) return false;
    const sourceKeys = ["source_title", "source_url", "source_sha256", "source_class", "locator", "rights"];
    if (row.source_id) {
      if (sourceKeys.some(key => !row[key].trim()) || !sourceLink(row.source_url) ||
        !/^[a-f0-9]{64}$/.test(row.source_sha256) ||
        ![...native, "tool_rendered_author_page_lead", "native_discovery_registry_json"].includes(row.source_class)) return false;
    } else if (sourceKeys.some(key => row[key])) return false;
    if (row.selection === "selected" && (!row.value.trim() || !row.source_id || !native.includes(row.source_class))) return false;
    if (!["selected", "held"].includes(row.selection) && row.value) return false;
    if (row.selection === "held" && row.value && !row.source_id) return false;
    if (!date(row.source_document_date) || !date(row.source_capture_date) || related(row.related_evidence) === null) return false;
    if (row.field === "first_criticality" && row.value) {
      return date(row.value) && row.date_precision === {4: "year", 7: "month", 10: "day"}[row.value.length] &&
        !(row.selection === "selected" && row.source_capture_date.length === 10 && row.value > row.source_capture_date);
    }
    return !row.date_precision;
  }

  /** Render every reviewed disposition, keeping held values separate from selected cells.
   * @param {unknown} assertions Original ledger rows attached to one map facility.
   * @returns {string} Escaped detail HTML, an empty section or a safe refusal.
   */
  function render(assertions) {
    if (!Array.isArray(assertions)) return refusal;
    if (!assertions.length) return "";
    if (assertions.some(row => !valid(row)) || new Set(assertions.map(row => `${row.stable_id}:${row.field}`)).size !== assertions.length ||
      new Set(assertions.map(row => row.stable_id)).size !== 1) return refusal;
    return '<section class="field-sources primary-research-sources"><h3>Primary research decisions</h3><p>Held claims do not fill the reactor record. Event precision, document dates and retrieval dates describe different things.</p>' +
      assertions.map(row => `<details><summary>${escape(fields[row.field])}: ${escape(decisions[row.selection])}${row.value ? ` · ${escape(row.value)}` : ""}</summary><p>${escape(row.scope)}</p><p>${escape(row.assertion_basis)}</p>${row.date_precision ? `<p>Event precision: ${escape(row.date_precision)}</p>` : ""}${row.source_id ? `<p>${escape(row.source_title)} · document ${escape(row.source_document_date || "date unknown")} · retrieved ${escape(row.source_capture_date || "date unknown")}</p><p>Location in source: ${escape(row.locator)}</p><p>Rights: ${escape(row.rights)}</p><p>Original source SHA-256: ${escape(row.source_sha256)}</p><a href="${escape(row.source_url)}" target="_blank" rel="noopener">Original source ↗</a>` : '<p>No admissible original source supplies this field.</p>'}${related(row.related_evidence).map(citation => `<p>Related evidence: ${escape(citation.source_id)} · ${escape(citation.locator || "location not supplied")} · ${escape(citation.admissibility || "scope not supplied")}${citation.reported_value ? ` · reported ${escape(citation.reported_value)}` : ""} · SHA-256 ${escape(citation.sha256)} <a href="${escape(citation.original_url)}" target="_blank" rel="noopener">Source ↗</a></p>`).join("")}</details>`).join("") + '</section>';
  }

  const api = Object.freeze({render});
  globalThis.PrimaryResearchAssertions = api;
  if (typeof module !== "undefined") module.exports = api;
})();
