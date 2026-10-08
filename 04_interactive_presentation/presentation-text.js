// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original display text and source-link rendering.
"use strict";

/**
 * Original source-link cells accepted by the maintained presentation.
 * @typedef {string|{url: string, title?: string}|null|undefined} AtlasSourceLink
 */

/**
 * Original link array whose cells this reader never changes.
 * @typedef {import("./browser-contracts.js").AtlasReadonlyArray<AtlasSourceLink>} AtlasSourceLinks
 */

/** Original text/link renderer shared by actual browser and native callers. */
var AtlasPresentationText = (() => {
  /** @type {Record<string, string>} */
  const entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  /**
   * Retain the original native string representation while escaping HTML metacharacters.
   * @param {unknown} value Original displayed cell, including explicit missing values.
   * @returns {string} Escaped original representation without markup interpretation.
   */
  function escape(value) {
    return String(value).replace(
      /[&<>"']/g,
      (character) => entities[character],
    );
  }
  /**
   * Retain the original HTTP(S) link policy without filling missing source URLs.
   * @param {string|undefined} value Original supplied URL or missing source cell.
   * @returns {string} Original escaped HTTP(S) URL or refused-link marker.
   */
  function safeUrl(value) {
    try {
      const url = new URL(String(value));
      return ["https:", "http:"].includes(url.protocol)
        ? escape(url.href)
        : "#";
    } catch {
      return "#";
    }
  }
  /**
   * Select only actual present original links before accessing their source fields.
   * @param {AtlasSourceLink} value Original source-reference cell.
   * @returns {value is NonNullable<AtlasSourceLink>} Missing and empty cells are absent.
   */
  function presentSource(value) {
    return value !== undefined && value !== null && value !== "";
  }
  /**
   * Retain original source order, duplicate identities, titles and link escaping.
   * @param {AtlasSourceLinks|undefined|null} values Original source-reference cells.
   * @returns {string} Original rendered source links without new source assertions.
   */
  function sourceLinks(values) {
    return [...new Set((values || []).filter(presentSource))]
      .map((source) => {
        const url = typeof source === "string" ? source : source.url;
        return `<a href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">${escape(typeof source === "string" ? source : source.title || url)} ↗</a>`;
      })
      .join("");
  }
  return Object.freeze({ escape, safeUrl, sourceLinks });
})();

globalThis.AtlasPresentationText = AtlasPresentationText;
