// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — validated taxonomy source citations
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { createHash } = require("node:crypto");
const { isDeepStrictEqual } = require("node:util");
const VALUE_FIELDS = [
  "name", "kind", "family", "principle", "strength", "challenge",
  "maturity", "evidence", "source_urls",
];
const TOPICS = new Set([
  "classification", "fuel-state-classification", "historical-operation", "operating-mode",
  "principle", "strength", "challenge",
]);
const FIELD_TOPICS = new Set(["principle", "strength", "challenge"]);

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

function requireKeys(value, fields, label) {
  requireValue(value !== null && typeof value === "object" && !Array.isArray(value), `${label}: expected an object`);
  requireValue(isDeepStrictEqual(Object.keys(value).sort(), [...fields].sort()), `${label}: unexpected fields`);
}

function requireText(value, label) {
  requireValue(typeof value === "string" && value.length > 0 && value === value.trim() && !/[\t\r\n]/.test(value), `${label}: expected nonempty single-line text`);
}

function requireUrl(value) {
  requireText(value, "Source URL");
  requireValue(/^https:\/\/[a-zA-Z0-9.-]+\/[\S]*$/.test(value), "Source URL: expected anonymous HTTPS");
}

function requireArray(value, label) {
  requireValue(Array.isArray(value), `${label}: expected an array`);
}

/**
 * Read and validate all citations before a taxonomy export writes any product.
 *
 * @param {string} repositoryRoot Canonical candidate or complete isolated copy.
 * @param {Array<object>} rows Actual entries loaded from taxonomy-expanded.js.
 * @returns {Map<string, Array<object>>} Entry IDs mapped to resolved source citations.
 * @throws {Error} On missing, malformed, stale, duplicate or incomplete metadata.
 *
 * A source-inspected statement is partial support. This contract never grants
 * complete entry review, scientific acceptance or rights to redistribute originals.
 * Bound fields must have their declared text/URL types; physical statements and
 * their source URLs must match the actual entry. A retained
 * source with unknown original retrieval time keeps captured_at null.
 * PDF sources require page locators. HTML and XML sources use sections with
 * zero page counts and empty PDF/printed page arrays.
 */
function readCitations(repositoryRoot, rows) {
  const metadataPath = path.join(repositoryRoot, "metadata/taxonomy_audit/claim_citations.json");
  const document = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  requireKeys(document, ["schema_version", "taxonomy_sha256", "sources", "records"], "Citations");
  requireValue(document.schema_version === "1.2.0", "Citations: unsupported schema");
  const taxonomy = fs.readFileSync(path.join(repositoryRoot, "04_interactive_presentation/data/taxonomy-expanded.js"));
  requireValue(document.taxonomy_sha256 === createHash("sha256").update(taxonomy).digest("hex"), "Citations: stale taxonomy hash");
  requireArray(rows, "Taxonomy entries");
  requireArray(document.sources, "Citation sources");
  requireArray(document.records, "Citation records");
  requireValue(rows.length > 0 && document.records.length === rows.length, "Citations: incomplete entry set");
  const sources = new Map();
  for (const source of document.sources) {
    requireKeys(source, ["id", "title", "url", "sha256", "captured_at", "capture_method", "format", "page_count", "access"], "Citation source");
    requireText(source.id, "Source ID");
    requireValue(!sources.has(source.id), "Citations: duplicate source ID");
    requireText(source.title, "Source title");
    requireUrl(source.url);
    requireValue(typeof source.sha256 === "string" && /^[a-f0-9]{64}$/.test(source.sha256), "Source: invalid SHA-256");
    requireValue(source.capture_method === "publisher-tls" || source.capture_method === "retained-source-review", "Source: unsupported capture method");
    if (source.capture_method === "publisher-tls") {
      requireValue(typeof source.captured_at === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/.test(source.captured_at) && Number.isFinite(Date.parse(source.captured_at)) && new Date(source.captured_at).toISOString().slice(0, 19) === source.captured_at.slice(0, 19), "Source: invalid UTC capture time");
    } else {
      requireValue(source.captured_at === null, "Source: original capture time is unknown for retained-source review");
    }
    requireValue(source.access === "catalogue-only; original not redistributed", "Source: unsupported custody claim");
    requireValue(source.format === "pdf" || source.format === "html" || source.format === "xml", "Source: unsupported format");
    requireValue(Number.isInteger(source.page_count) && (source.format === "pdf" ? source.page_count > 0 : source.page_count === 0), "Source: invalid page count");
    sources.set(source.id, source);
  }
  const citationsById = new Map();
  const citationIds = new Set();
  const usedSources = new Set();
  for (const [index, record] of document.records.entries()) {
    requireKeys(record, ["id", "values", "complete_entry_review", "citations"], "Citation record");
    requireText(record.id, "Entry ID");
    requireValue(record.id === rows[index].id && !citationsById.has(record.id), "Citations: entry identity or order mismatch");
    requireKeys(record.values, VALUE_FIELDS, "Bound taxonomy values");
    for (const field of VALUE_FIELDS.filter(field => field !== "source_urls")) requireText(record.values[field], `Bound taxonomy ${field}`);
    requireArray(record.values.source_urls, "Bound taxonomy source URLs");
    requireValue(record.values.source_urls.length > 0, "Bound taxonomy: missing source URLs");
    for (const url of record.values.source_urls) requireUrl(url);
    const expected = Object.fromEntries(VALUE_FIELDS.map(field => [field, rows[index][field]]));
    requireValue(isDeepStrictEqual(record.values, expected), "Citations: changed taxonomy values");
    requireValue(record.complete_entry_review === false, "Citations: complete entry review is not established");
    requireArray(record.citations, "Entry citations");
    const resolved = [];
    for (const citation of record.citations) {
      requireKeys(citation, ["id", "topic", "statement", "source_id", "section", "pdf_pages", "printed_pages", "scope", "reviewed_on", "review_basis"], "Citation");
      requireText(citation.id, "Citation ID");
      requireValue(!citationIds.has(citation.id), "Citations: duplicate citation ID");
      requireValue(TOPICS.has(citation.topic) && citation.id.startsWith(`${record.id}:${citation.topic}:`), "Citation: topic or identity mismatch");
      for (const field of ["statement", "section", "scope"]) requireText(citation[field], `Citation ${field}`);
      requireValue(!FIELD_TOPICS.has(citation.topic) || citation.statement === record.values[citation.topic], "Citation: statement differs from the complete physical field");
      requireValue(citation.review_basis === "author-source-inspection", "Citation: unsupported review basis");
      requireValue(typeof citation.reviewed_on === "string" && /^\d{4}-\d{2}-\d{2}$/.test(citation.reviewed_on) && Number.isFinite(Date.parse(citation.reviewed_on)) && new Date(citation.reviewed_on).toISOString().slice(0, 10) === citation.reviewed_on, "Citation: invalid review date");
      const source = sources.get(citation.source_id);
      requireValue(source !== undefined, "Citation: unknown source ID");
      requireValue(!FIELD_TOPICS.has(citation.topic) || record.values.source_urls.includes(source.url), "Citation: physical source absent from entry references");
      requireValue(source.captured_at === null || citation.reviewed_on >= source.captured_at.slice(0, 10), "Citation: review predates source capture");
      requireArray(citation.pdf_pages, "PDF pages");
      requireArray(citation.printed_pages, "Printed pages");
      requireValue(new Set(citation.pdf_pages).size === citation.pdf_pages.length, "Citation: duplicate PDF page");
      requireValue(source.format === "pdf" ? citation.pdf_pages.length > 0 && citation.printed_pages.length === citation.pdf_pages.length : citation.pdf_pages.length === 0 && citation.printed_pages.length === 0, "Citation: inconsistent page locator");
      for (const page of citation.pdf_pages) requireValue(Number.isInteger(page) && page > 0 && page <= source.page_count, "Citation: PDF page outside source");
      for (const page of citation.printed_pages) requireText(page, "Printed page");
      citationIds.add(citation.id);
      usedSources.add(source.id);
      resolved.push({ ...citation, source_title: source.title, source_url: source.url, source_sha256: source.sha256,
        source_capture_method: source.capture_method, source_captured_at: source.captured_at });
    }
    citationsById.set(record.id, resolved);
  }
  requireValue(usedSources.size === sources.size, "Citations: unused source metadata");
  return citationsById;
}

module.exports = { readCitations };
