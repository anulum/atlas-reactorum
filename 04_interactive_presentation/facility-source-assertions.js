// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — accepted research field source rendering
"use strict";

/**
 * Original field assertion after all producer columns and source links are checked.
 * @typedef {object} FacilityFieldOrigin
 * @property {string} field Original field identity.
 * @property {string} value Verbatim accepted source value.
 * @property {string} source_dataset Original table identity.
 * @property {string} source_sha256 Original source digest.
 * @property {string} source_url Anonymous HTTPS source locator.
 * @property {string} source_role Original source role, possibly unspecified.
 * @property {string} source_capture_date Retrieval date, never an inferred event date.
 * @property {string} license Original source rights, possibly unspecified.
 * @property {string} scope Original support boundary, possibly unspecified.
 * @property {string} selection Selected or superseded assertion disposition.
 */

/** Original field-source renderer shared by browser and native consumers. */
var FacilitySourceAssertions = (() => {
  const keys = [
    "field",
    "value",
    "source_dataset",
    "source_sha256",
    "source_url",
    "source_role",
    "source_capture_date",
    "license",
    "scope",
    "selection",
  ];
  /** @type {Record<string, string>} */
  const labels = {
    operator: "Operator",
    purpose: "Purpose",
    first_criticality: "First criticality",
  };
  /** @type {Record<string, string>} */
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  const refusal =
    '<p role="status">Research field sources are unavailable.</p>';

  /**
   * Escape original source text before inserting it into the facility detail.
   * @param {string} value Original cell or source metadata.
   * @returns {string} Text safe for HTML text and quoted attributes.
   */
  function escape(value) {
    return value.replace(/[&<>"']/g, (character) => entities[character]);
  }

  /**
   * Require an anonymous HTTPS link without exposing parser diagnostics.
   * @param {string} value Original source URL.
   * @returns {boolean} Whether the link is anonymous and uses HTTPS.
   */
  function sourceLink(value) {
    if (!/^https:\/\/[^/\\\s]/.test(value)) return false;
    try {
      const url = new URL(value);
      return (
        url.protocol === "https:" &&
        !!url.hostname &&
        !url.username &&
        !url.password
      );
    } catch {
      return false;
    }
  }

  /**
   * Render original accepted values, including superseded source assertions.
   * @param {unknown} origins Serialized original field assertions.
   * @returns {string} Escaped source details, an empty section or a safe refusal.
   */
  function render(origins) {
    if (!Array.isArray(origins)) return refusal;
    if (!origins.length) return "";
    const candidates = /** @type {unknown[]} */ (origins);
    if (
      candidates.some((row) => {
        if (!row || typeof row !== "object") return true;
        const cells = /** @type {Record<string, unknown>} */ (row);
        return (
          Object.keys(row).length !== keys.length ||
          keys.some((key) => typeof cells[key] !== "string") ||
          !validTextRow(/** @type {FacilityFieldOrigin} */ (row))
        );
      })
    )
      return refusal;
    const checked = /** @type {FacilityFieldOrigin[]} */ (candidates);
    return (
      '<section class="field-sources"><h3>Research field sources</h3>' +
      "<p>These are the original source assertions. Retrieval dates are not publication or reactor event dates; superseded assertions remain visible.</p>" +
      checked
        .map(
          (row) =>
            `<details><summary>${escape(labels[row.field])}: ${escape(row.value)} · ${row.selection === "selected" ? "Selected value" : "Previous source assertion"}</summary><p>${escape(row.source_role || "Source role not specified")} · retrieved ${escape(row.source_capture_date || "date unknown")} · ${escape(row.license || "Source rights not specified")}</p><p>${escape(row.scope || "Source scope not specified")}</p><p>Original table: ${escape(row.source_dataset)} · SHA-256 ${escape(row.source_sha256)}</p><a href="${escape(row.source_url)}" target="_blank" rel="noopener">Original source ↗</a></details>`,
        )
        .join("") +
      "</section>"
    );
  }

  /**
   * Check source meaning after the complete textual column shape is established.
   * @param {FacilityFieldOrigin} row Actual original text cells, not unchecked JSON.
   * @returns {boolean} Whether field, digest, selection, table and source are admissible.
   */
  function validTextRow(row) {
    return (
      Object.hasOwn(labels, row.field) &&
      !!row.value &&
      /^[a-f0-9]{64}$/.test(row.source_sha256) &&
      ["selected", "superseded"].includes(row.selection) &&
      !!row.source_dataset &&
      sourceLink(row.source_url)
    );
  }

  return Object.freeze({ render });
})();
globalThis.FacilitySourceAssertions = FacilitySourceAssertions;
if (typeof module !== "undefined") module.exports = FacilitySourceAssertions;
