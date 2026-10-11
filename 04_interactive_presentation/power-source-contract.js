// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — power documentary custody and date admission
"use strict";

/**
 * Original power source custody; capture attempts cannot support selected facts.
 * @typedef {Record<string, unknown> & {
 * source_id:string,url:string,requested_url:string,captured_at:string,
 * body_sha256:string,body_bytes:number|null,http_status:number|null,
 * body_complete:boolean,native_class:string,body_state:string,
 * eligible_for_selection:boolean,rights_scope:string
 * }} PowerSourceRecord
 */
/**
 * Original documentary locator and date meaning, separate from capture time.
 * @typedef {Record<string, unknown> & {
 * source_id:string,locator:string,document_date:string,date_precision:string,date_basis:string
 * }} PowerCitation
 */

/** Native source admission shared by the browser and Node consumers. */
var PowerSourceContract = (() => {
  const nativeClasses = new Set([
    "native_original_pdf",
    "native_original_html",
    "native_original_facsimile",
    "native_original_spreadsheet",
  ]);

  /**
   * Require an object before reading original source cells.
   * @param {unknown} value Original JSON input.
   * @returns {Record<string, unknown>} Original object after shape admission.
   */
  function mapping(value) {
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error("power admission requires an object with string keys");
    return /** @type {Record<string, unknown>} */ (value);
  }
  /**
   * Require an explicit array without scalar coercion.
   * @param {unknown} value Original JSON input.
   * @returns {unknown[]} Original array.
   */
  function sequence(value) {
    if (!Array.isArray(value))
      throw new Error("power admission requires an array");
    return /** @type {unknown[]} */ (value);
  }
  /**
   * Require an original textual cell.
   * @param {Record<string, unknown>} row Original object.
   * @param {string} field Exact field identity.
   * @param {boolean} empty Whether this cell may explicitly remain empty.
   * @returns {string} Original text.
   */
  function text(row, field, empty = false) {
    const value = row[field];
    if (typeof value !== "string" || (!empty && !value.trim()))
      throw new Error("power admission requires text: " + field);
    return value;
  }
  /**
   * Require an original lowercase SHA-256 binding.
   * @param {unknown} value Original digest.
   * @returns {string} Original admitted digest.
   */
  function digest(value) {
    if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value))
      throw new Error("power admission requires a SHA-256 binding");
    return value;
  }
  /**
   * Require a credential-free HTTPS document or attempt locator.
   * @param {unknown} value Original URL.
   * @returns {string} Original admitted URL.
   */
  function httpsUrl(value) {
    if (typeof value !== "string")
      throw new Error("power source URL must be text");
    const parsed = new URL(value);
    if (
      parsed.protocol !== "https:" ||
      !parsed.hostname ||
      parsed.username ||
      parsed.password
    )
      throw new Error("power source URL must be credential-free HTTPS");
    return value;
  }
  /**
   * Check a calendar day without accepting JavaScript date normalisation.
   * @param {string} value Exact four-digit-year ISO calendar day.
   * @returns {boolean} True only for the unchanged valid day.
   */
  function day(value) {
    const instant = new Date(value + "T00:00:00Z");
    return (
      Number(value.slice(0, 4)) > 0 &&
      Number.isFinite(instant.getTime()) &&
      instant.toISOString().slice(0, 10) === value
    );
  }
  /**
   * Preserve documentary precision and basis independently of capture time.
   * @param {Record<string, unknown>} row Original citation date fields.
   * @returns {void} Every documentary date retains its declared meaning.
   */
  function documentDate(row) {
    const value = text(row, "document_date", true);
    const precision = text(row, "date_precision");
    text(row, "date_basis");
    if (precision === "unknown") {
      if (value) throw new Error("unknown power document date must be empty");
      return;
    }
    if (precision === "month_range") {
      if (!/^\d{4}-\d{2}\/\d{4}-\d{2}$/.test(value))
        throw new Error("power documentary month range is malformed");
      const [start, end] = value.split("/");
      if (!day(start + "-01") || !day(end + "-01"))
        throw new Error("power documentary month range is invalid");
      if (start > end)
        throw new Error("power documentary month range is reversed");
      return;
    }
    /** @type {Record<string, {pattern:RegExp,suffix:string}>} */
    const formats = {
      year: { pattern: /^\d{4}$/, suffix: "-01-01" },
      month: { pattern: /^\d{4}-\d{2}$/, suffix: "-01" },
      day: { pattern: /^\d{4}-\d{2}-\d{2}$/, suffix: "" },
    };
    const format = Object.hasOwn(formats, precision)
      ? formats[precision]
      : undefined;
    if (!format || !format.pattern.test(value))
      throw new Error("power document date differs from its precision");
    if (!day(value + format.suffix))
      throw new Error("power document date is invalid");
  }
  /**
   * Require explicit native-document eligibility or retain a failed capture.
   * @param {unknown} input Original source metadata array.
   * @returns {Map<string, PowerSourceRecord>} Unique original custody records.
   */
  function admitSources(input) {
    /** @type {Map<string, PowerSourceRecord>} */
    const result = new Map();
    for (const item of sequence(input)) {
      const row = mapping(item),
        identity = text(row, "source_id");
      if (result.has(identity))
        throw new Error("duplicate power source identity");
      httpsUrl(row.url);
      httpsUrl(row.requested_url);
      const captured = text(row, "captured_at");
      if (
        !/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,6})?(?:Z|\+00:00)$/.test(
          captured,
        )
      )
        throw new Error(
          "power capture timestamp must use canonical UTC ISO format",
        );
      const instant = new Date(captured);
      if (
        !Number.isFinite(instant.getTime()) ||
        Number(captured.slice(0, 4)) === 0 ||
        instant.toISOString().slice(0, 19) !== captured.slice(0, 19)
      )
        throw new Error("power capture timestamp is invalid");
      if (typeof row.eligible_for_selection !== "boolean")
        throw new Error("power source eligibility must be explicit");
      if (typeof row.body_complete !== "boolean")
        throw new Error("power source body completeness must be explicit");
      if (
        row.http_status !== null &&
        (typeof row.http_status !== "number" ||
          !Number.isInteger(row.http_status) ||
          row.http_status < 100 ||
          row.http_status > 599)
      )
        throw new Error("power source HTTP status is invalid");
      if (
        row.body_bytes !== null &&
        (typeof row.body_bytes !== "number" ||
          !Number.isSafeInteger(row.body_bytes) ||
          row.body_bytes < 0)
      )
        throw new Error("power source body byte count is invalid");
      const bodyHash = text(row, "body_sha256", true);
      if (bodyHash) digest(bodyHash);
      const state = text(row, "body_state"),
        nativeClass = text(row, "native_class", true);
      if (
        !["qualified_document", "context_only", "capture_attempt"].includes(
          state,
        )
      )
        throw new Error("power source body state is invalid");
      if (state !== "capture_attempt") {
        if (
          row.http_status !== 200 ||
          row.body_complete !== true ||
          !Number.isInteger(row.body_bytes) ||
          typeof row.body_bytes !== "number" ||
          row.body_bytes <= 0 ||
          !nativeClasses.has(nativeClass)
        )
          throw new Error(
            "power documentary context needs a complete native document",
          );
        digest(row.body_sha256);
      }
      if (row.eligible_for_selection) {
        if (state !== "qualified_document")
          throw new Error(
            "selected power source needs documentary qualification",
          );
      } else if (state === "qualified_document")
        throw new Error(
          "qualified power document cannot lack selection eligibility",
        );
      if (text(row, "rights_scope") !== "citation_and_factual_metadata_only")
        throw new Error(
          "power source rights must exclude original body redistribution",
        );
      result.set(identity, /** @type {PowerSourceRecord} */ (row));
    }
    return result;
  }
  /**
   * Bind documentary citations while excluding attempts from factual support.
   * @param {unknown} input Original citation array.
   * @param {Map<string, PowerSourceRecord>} sources Admitted original registry.
   * @param {boolean} selected Whether citations support a selected scalar.
   * @returns {PowerCitation[]} Original admitted citations.
   */
  function admitCitations(input, sources, selected) {
    /** @type {PowerCitation[]} */
    const result = [];
    const seen = new Set();
    for (const item of sequence(input)) {
      const row = mapping(item),
        identity = text(row, "source_id"),
        locator = text(row, "locator"),
        source = sources.get(identity);
      if (!source || source.body_state === "capture_attempt")
        throw new Error(
          "power citation requires a retained documentary context",
        );
      if (selected && source.eligible_for_selection !== true)
        throw new Error("power selected citation is not qualified");
      const key = JSON.stringify([identity, locator]);
      if (seen.has(key)) throw new Error("duplicate power citation");
      seen.add(key);
      documentDate(row);
      result.push(/** @type {PowerCitation} */ (row));
    }
    if (selected && !result.length)
      throw new Error("selected power value requires a source citation");
    return result;
  }
  return Object.freeze({
    mapping,
    sequence,
    text,
    digest,
    httpsUrl,
    documentDate,
    admitSources,
    admitCitations,
  });
})();
globalThis.PowerSourceContract = PowerSourceContract;
if (typeof module !== "undefined") module.exports = PowerSourceContract;
