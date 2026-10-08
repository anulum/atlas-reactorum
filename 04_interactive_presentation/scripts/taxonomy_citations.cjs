// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — validated taxonomy source citations
"use strict";

/**
 * Original publisher or retained-copy description, validated before resolution.
 * @typedef {object} CitationSource
 * @property {string} id Source registry identity.
 * @property {string} title Original source title.
 * @property {string} url Anonymous HTTPS citation URL.
 * @property {string} sha256 Recorded original source digest.
 * @property {string|null} captured_at Actual UTC retrieval or unknown retained-copy retrieval.
 * @property {"publisher-tls"|"retained-source-review"} capture_method Acquisition custody.
 * @property {"pdf"|"html"|"xml"} format Source format governing page locators.
 * @property {number} page_count Positive PDF count, or zero for HTML/XML.
 * @property {"catalogue-only; original not redistributed"} access Explicit distribution boundary.
 */

/**
 * Source-inspected claim with its original event, locator and review meanings.
 * @typedef {object} Citation
 * @property {string} id Entry, topic and claim identity.
 * @property {string} topic Accepted citation topic.
 * @property {string} statement Exact original statement or complete bound physical field.
 * @property {string} source_id Original source registry identity.
 * @property {string} section Original section locator.
 * @property {number[]} pdf_pages Distinct one-based pages within the source PDF.
 * @property {string[]} printed_pages Original printed page labels in PDF locator order.
 * @property {string} scope Source-specific support boundary.
 * @property {string} reviewed_on Actual UTC review date, distinct from retrieval.
 * @property {"author-source-inspection"} review_basis Recorded review basis, not independent acceptance.
 */

/**
 * Original claim with the validated registry attributes consumed by exports.
 * @typedef {Citation & {
 * source_title: string, source_url: string, source_sha256: string,
 * source_capture_method: CitationSource["capture_method"],
 * source_captured_at: CitationSource["captured_at"]
 * }} ResolvedCitation
 */

const fs = require("node:fs");
const path = require("node:path");
const { createHash } = require("node:crypto");
const { isDeepStrictEqual } = require("node:util");
const VALUE_FIELDS = [
  "name",
  "kind",
  "family",
  "principle",
  "strength",
  "challenge",
  "maturity",
  "evidence",
  "source_urls",
];
const TOPICS = new Set([
  "classification",
  "fuel-state-classification",
  "historical-operation",
  "operating-mode",
  "principle",
  "strength",
  "challenge",
]);
const FIELD_TOPICS = new Set(["principle", "strength", "challenge"]);

/**
 * Refuse a failed source-bound invariant before products can be written.
 * @param {unknown} condition Actual invariant result; truthiness is the original contract.
 * @param {string} message Deliberately authored contract refusal.
 * @returns {asserts condition} Narrow the condition only after its actual check succeeds.
 * @throws {Error} The supplied invariant is false.
 */
function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

/**
 * Require an object with exactly the original schema's own keys.
 * @param {unknown} value Parsed metadata before validation.
 * @param {readonly string[]} fields Complete required key set.
 * @param {string} label Owning contract label.
 * @returns {asserts value is Record<string, unknown>} Object cells remain unknown until checked.
 * @throws {Error} The value is absent, an array or has changed keys.
 */
function requireKeys(value, fields, label) {
  requireValue(
    value !== null && typeof value === "object" && !Array.isArray(value),
    `${label}: expected an object`,
  );
  requireValue(
    isDeepStrictEqual(Object.keys(value).sort(), [...fields].sort()),
    `${label}: unexpected fields`,
  );
}

/**
 * Retain unpadded, nonempty single-line source wording.
 * @param {unknown} value Original metadata cell.
 * @param {string} label Owning field label.
 * @returns {asserts value is string} Original text after validation.
 * @throws {Error} The cell is not valid source text.
 */
function requireText(value, label) {
  requireValue(
    typeof value === "string" &&
      value.length > 0 &&
      value === value.trim() &&
      !/[\t\r\n]/.test(value),
    `${label}: expected nonempty single-line text`,
  );
}

/**
 * Require the citation contract's anonymous HTTPS locator.
 * @param {unknown} value Original URL cell before checking.
 * @returns {asserts value is string} Original URL, without normalising or rewriting it.
 * @throws {Error} Text or anonymous HTTPS custody is invalid.
 */
function requireUrl(value) {
  requireText(value, "Source URL");
  requireValue(
    /^https:\/\/[a-zA-Z0-9.-]+\/[\S]*$/.test(value),
    "Source URL: expected anonymous HTTPS",
  );
}

/**
 * Require a real metadata array without inferring its member types.
 * @param {unknown} value Parsed metadata cell.
 * @param {string} label Owning collection label.
 * @returns {asserts value is unknown[]} Original array; members still require validation.
 * @throws {Error} The cell is not an array.
 */
function requireArray(value, label) {
  requireValue(Array.isArray(value), `${label}: expected an array`);
}

/**
 * Read and validate all citations before a taxonomy export writes any product.
 * A source-inspected statement is partial support. This contract never grants
 * complete entry review, scientific acceptance or rights to redistribute originals.
 * Bound fields must have their declared text/URL types; physical statements and
 * their source URLs must match the actual entry. A retained
 * source with unknown original retrieval time keeps captured_at null.
 * PDF sources require page locators. HTML and XML sources use sections with
 * zero page counts and empty PDF/printed page arrays.
 * @param {string} repositoryRoot Canonical candidate or complete isolated copy.
 * @param {unknown} rows Actual entries loaded from taxonomy-expanded.js before validation.
 * @returns {Map<string, ResolvedCitation[]>} Entry IDs mapped to resolved source citations.
 * @throws {Error} On missing, malformed, stale, duplicate or incomplete metadata.
 */
function readCitations(repositoryRoot, rows) {
  const metadataPath = path.join(
    repositoryRoot,
    "metadata/taxonomy_audit/claim_citations.json",
  );
  /** @type {unknown} */
  const document = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  requireKeys(
    document,
    ["schema_version", "taxonomy_sha256", "sources", "records"],
    "Citations",
  );
  requireValue(
    document.schema_version === "1.2.0",
    "Citations: unsupported schema",
  );
  const taxonomy = fs.readFileSync(
    path.join(
      repositoryRoot,
      "04_interactive_presentation/data/taxonomy-expanded.js",
    ),
  );
  requireValue(
    document.taxonomy_sha256 ===
      createHash("sha256").update(taxonomy).digest("hex"),
    "Citations: stale taxonomy hash",
  );
  requireArray(rows, "Taxonomy entries");
  requireArray(document.sources, "Citation sources");
  requireArray(document.records, "Citation records");
  requireValue(
    rows.length > 0 && document.records.length === rows.length,
    "Citations: incomplete entry set",
  );
  /** @type {Map<string, CitationSource>} */
  const sources = new Map();
  for (const source of document.sources) {
    requireKeys(
      source,
      [
        "id",
        "title",
        "url",
        "sha256",
        "captured_at",
        "capture_method",
        "format",
        "page_count",
        "access",
      ],
      "Citation source",
    );
    requireText(source.id, "Source ID");
    requireValue(!sources.has(source.id), "Citations: duplicate source ID");
    requireText(source.title, "Source title");
    requireUrl(source.url);
    requireValue(
      typeof source.sha256 === "string" && /^[a-f0-9]{64}$/.test(source.sha256),
      "Source: invalid SHA-256",
    );
    requireValue(
      source.capture_method === "publisher-tls" ||
        source.capture_method === "retained-source-review",
      "Source: unsupported capture method",
    );
    if (source.capture_method === "publisher-tls") {
      requireValue(
        typeof source.captured_at === "string" &&
          /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/.test(
            source.captured_at,
          ) &&
          Number.isFinite(Date.parse(source.captured_at)) &&
          new Date(source.captured_at).toISOString().slice(0, 19) ===
            source.captured_at.slice(0, 19),
        "Source: invalid UTC capture time",
      );
    } else {
      requireValue(
        source.captured_at === null,
        "Source: original capture time is unknown for retained-source review",
      );
    }
    requireValue(
      source.access === "catalogue-only; original not redistributed",
      "Source: unsupported custody claim",
    );
    requireValue(
      source.format === "pdf" ||
        source.format === "html" ||
        source.format === "xml",
      "Source: unsupported format",
    );
    requireValue(
      typeof source.page_count === "number" &&
        Number.isInteger(source.page_count) &&
        (source.format === "pdf"
          ? source.page_count > 0
          : source.page_count === 0),
      "Source: invalid page count",
    );
    sources.set(source.id, /** @type {CitationSource} */ (source));
  }
  /** @type {Map<string, ResolvedCitation[]>} */
  const citationsById = new Map();
  /** @type {Set<string>} */
  const citationIds = new Set();
  /** @type {Set<string>} */
  const usedSources = new Set();
  for (const [index, record] of document.records.entries()) {
    requireKeys(
      record,
      ["id", "values", "complete_entry_review", "citations"],
      "Citation record",
    );
    requireText(record.id, "Entry ID");
    const entry = rows[index];
    requireValue(
      entry !== null && typeof entry === "object" && !Array.isArray(entry),
      "Taxonomy entry: expected an object",
    );
    const originalEntry = /** @type {Record<string, unknown>} */ (entry);
    requireValue(
      record.id === originalEntry.id && !citationsById.has(record.id),
      "Citations: entry identity or order mismatch",
    );
    requireKeys(record.values, VALUE_FIELDS, "Bound taxonomy values");
    for (const field of VALUE_FIELDS.filter((field) => field !== "source_urls"))
      requireText(record.values[field], `Bound taxonomy ${field}`);
    requireArray(record.values.source_urls, "Bound taxonomy source URLs");
    requireValue(
      record.values.source_urls.length > 0,
      "Bound taxonomy: missing source URLs",
    );
    for (const url of record.values.source_urls) requireUrl(url);
    const expected = Object.fromEntries(
      VALUE_FIELDS.map((field) => [field, originalEntry[field]]),
    );
    requireValue(
      isDeepStrictEqual(record.values, expected),
      "Citations: changed taxonomy values",
    );
    requireValue(
      record.complete_entry_review === false,
      "Citations: complete entry review is not established",
    );
    requireArray(record.citations, "Entry citations");
    /** @type {ResolvedCitation[]} */
    const resolved = [];
    for (const citation of record.citations) {
      requireKeys(
        citation,
        [
          "id",
          "topic",
          "statement",
          "source_id",
          "section",
          "pdf_pages",
          "printed_pages",
          "scope",
          "reviewed_on",
          "review_basis",
        ],
        "Citation",
      );
      requireText(citation.id, "Citation ID");
      requireValue(
        !citationIds.has(citation.id),
        "Citations: duplicate citation ID",
      );
      requireValue(
        typeof citation.topic === "string" &&
          TOPICS.has(citation.topic) &&
          citation.id.startsWith(`${record.id}:${citation.topic}:`),
        "Citation: topic or identity mismatch",
      );
      for (const field of ["statement", "section", "scope"])
        requireText(citation[field], `Citation ${field}`);
      requireValue(
        !FIELD_TOPICS.has(citation.topic) ||
          citation.statement === record.values[citation.topic],
        "Citation: statement differs from the complete physical field",
      );
      requireValue(
        citation.review_basis === "author-source-inspection",
        "Citation: unsupported review basis",
      );
      requireValue(
        typeof citation.reviewed_on === "string" &&
          /^\d{4}-\d{2}-\d{2}$/.test(citation.reviewed_on) &&
          Number.isFinite(Date.parse(citation.reviewed_on)) &&
          new Date(citation.reviewed_on).toISOString().slice(0, 10) ===
            citation.reviewed_on,
        "Citation: invalid review date",
      );
      requireValue(
        typeof citation.source_id === "string",
        "Citation: unknown source ID",
      );
      const source = sources.get(citation.source_id);
      requireValue(source !== undefined, "Citation: unknown source ID");
      requireValue(
        !FIELD_TOPICS.has(citation.topic) ||
          record.values.source_urls.includes(source.url),
        "Citation: physical source absent from entry references",
      );
      requireValue(
        source.captured_at === null ||
          citation.reviewed_on >= source.captured_at.slice(0, 10),
        "Citation: review predates source capture",
      );
      requireArray(citation.pdf_pages, "PDF pages");
      requireArray(citation.printed_pages, "Printed pages");
      requireValue(
        new Set(citation.pdf_pages).size === citation.pdf_pages.length,
        "Citation: duplicate PDF page",
      );
      requireValue(
        source.format === "pdf"
          ? citation.pdf_pages.length > 0 &&
              citation.printed_pages.length === citation.pdf_pages.length
          : citation.pdf_pages.length === 0 &&
              citation.printed_pages.length === 0,
        "Citation: inconsistent page locator",
      );
      for (const page of citation.pdf_pages)
        requireValue(
          typeof page === "number" &&
            Number.isInteger(page) &&
            page > 0 &&
            page <= source.page_count,
          "Citation: PDF page outside source",
        );
      for (const page of citation.printed_pages)
        requireText(page, "Printed page");
      citationIds.add(citation.id);
      usedSources.add(source.id);
      const originalCitation = /** @type {Citation} */ (citation);
      resolved.push({
        ...originalCitation,
        source_title: source.title,
        source_url: source.url,
        source_sha256: source.sha256,
        source_capture_method: source.capture_method,
        source_captured_at: source.captured_at,
      });
    }
    citationsById.set(record.id, resolved);
  }
  requireValue(
    usedSources.size === sources.size,
    "Citations: unused source metadata",
  );
  return citationsById;
}

module.exports = { readCitations };
