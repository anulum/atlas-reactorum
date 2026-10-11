// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — author assessment wire values and precise source date ranges.
"use strict";

/** @type {import("./author-review-contracts").AuthorReviewValues} Native wire admission shared by browser and Node readers. */
var AtlasAuthorReviewValues = (() => {
  /**
   * Require exactly the declared own object members before reading unknown cells.
   * @param {unknown} value Parsed input.
   * @param {readonly string[]} keys Complete wire members.
   * @returns {asserts value is Record<string,unknown>} Shape-admitted object with unknown cells.
   * @throws {Error} An object or its owned member set is invalid.
   */
  function object(value, keys) {
    if (
      !value ||
      typeof value !== "object" ||
      Array.isArray(value) ||
      Object.keys(value).length !== keys.length ||
      !keys.every((key) => Object.hasOwn(value, key))
    )
      throw new Error("Author review object shape is invalid");
  }
  /**
   * Require an actual array before validating its members.
   * @param {unknown} value Parsed collection.
   * @returns {asserts value is unknown[]} Original array without member inference.
   * @throws {Error} A collection is not an array.
   */
  function array(value) {
    if (!Array.isArray(value))
      throw new Error("Author review array is invalid");
  }
  /**
   * Admit nonempty single-line wording without changing source whitespace.
   * @param {unknown} value Original metadata cell.
   * @returns {asserts value is string} Text after wire admission.
   * @throws {Error} A cell lacks nonempty single-line text.
   */
  function text(value) {
    if (typeof value !== "string" || !value.length || /[\t\r\n]/.test(value))
      throw new Error("Author review text is invalid");
  }
  /**
   * Admit a distinct string-reference collection without reordering it.
   * @param {unknown} value Parsed references.
   * @returns {asserts value is string[]} Complete original reference array.
   * @throws {Error} A member is nontextual or duplicated.
   */
  function strings(value) {
    array(value);
    for (const member of value) text(member);
    if (new Set(value).size !== value.length)
      throw new Error("Author review references are duplicated");
  }
  /**
   * Require a lowercase stable editorial identity.
   * @param {unknown} value Original identity.
   * @returns {asserts value is string} Stable identity after admission.
   * @throws {Error} The identity grammar is invalid.
   */
  function identity(value) {
    if (typeof value !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value))
      throw new Error("Author review identity is invalid");
  }
  /**
   * Require a real four-digit-year calendar day without normalising overflow.
   * @param {unknown} value Full source date.
   * @returns {asserts value is string} Original valid YYYY-MM-DD value.
   * @throws {Error} The date shape or Gregorian calendar value is invalid.
   */
  function day(value) {
    if (
      typeof value !== "string" ||
      !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value) ||
      value.startsWith("0000") ||
      !Number.isFinite(Date.parse(value + "T00:00:00Z")) ||
      new Date(value + "T00:00:00Z").toISOString().slice(0, 10) !== value
    )
      throw new Error("Author review calendar date is invalid");
  }
  /**
   * Bound explicit year/month/day dates while retaining unknown precision.
   * @param {unknown} value Source date object before admission.
   * @returns {[string,string]|null} Inclusive declared date bounds or unknown.
   * @throws {Error} Date and precision disagree or are invalid.
   */
  function dateBounds(value) {
    object(value, ["value", "precision"]);
    if (value.value === null) {
      if (value.precision !== null)
        throw new Error("Unknown author date precision is invalid");
      return null;
    }
    text(value.value);
    if (value.precision === "day") {
      day(value.value);
      return [value.value, value.value];
    }
    if (
      value.precision === "month" &&
      /^[0-9]{4}-[0-9]{2}$/.test(value.value)
    ) {
      const first = value.value + "-01";
      day(first);
      const last = new Date(first + "T00:00:00Z");
      last.setUTCMonth(last.getUTCMonth() + 1);
      last.setUTCDate(0);
      return [first, last.toISOString().slice(0, 10)];
    }
    if (value.precision === "year" && /^[0-9]{4}$/.test(value.value)) {
      const first = value.value + "-01-01";
      day(first);
      return [first, value.value + "-12-31"];
    }
    throw new Error("Author review date precision is invalid");
  }
  /**
   * Admit recorded source custody without granting publisher rights.
   * @param {unknown} value Parsed source metadata.
   * @returns {import("./scripts/taxonomy_citations.cjs").CitationSource} Source after complete wire admission.
   * @throws {Error} Source shape, format, URL, hash, capture or rights are invalid.
   */
  function source(value) {
    object(value, [
      "id",
      "title",
      "url",
      "sha256",
      "captured_at",
      "capture_method",
      "format",
      "page_count",
      "access",
    ]);
    for (const key of ["id", "title", "url"]) text(value[key]);
    if (
      typeof value.url !== "string" ||
      !/^https:\/\/[a-zA-Z0-9.-]+\/\S*$/.test(value.url) ||
      typeof value.sha256 !== "string" ||
      !/^[a-f0-9]{64}$/.test(value.sha256)
    )
      throw new Error("Author review source locator or digest is invalid");
    if (value.capture_method === "retained-source-review") {
      if (value.captured_at !== null)
        throw new Error("Retained source acquisition remains unknown");
    } else if (value.capture_method === "publisher-tls") {
      if (
        typeof value.captured_at !== "string" ||
        !/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|\+00:00)$/.test(
          value.captured_at,
        ) ||
        !Number.isFinite(Date.parse(value.captured_at)) ||
        new Date(value.captured_at).toISOString().slice(0, 19) !==
          value.captured_at.slice(0, 19)
      )
        throw new Error("Author review source acquisition is invalid");
      day(value.captured_at.slice(0, 10));
    } else throw new Error("Author review source capture method is invalid");
    text(value.format);
    if (
      !["pdf", "html", "xml"].includes(value.format) ||
      typeof value.page_count !== "number" ||
      !Number.isInteger(value.page_count) ||
      (value.format === "pdf"
        ? value.page_count < 1
        : value.page_count !== 0) ||
      value.access !== "catalogue-only; original not redistributed"
    )
      throw new Error("Author review source format or custody is invalid");
    return /** @type {import("./scripts/taxonomy_citations.cjs").CitationSource} */ (
      value
    );
  }
  return Object.freeze({
    object,
    array,
    text,
    strings,
    identity,
    day,
    dateBounds,
    source,
  });
})();
globalThis.AtlasAuthorReviewValues = AtlasAuthorReviewValues;
if (typeof module !== "undefined") module.exports = AtlasAuthorReviewValues;
