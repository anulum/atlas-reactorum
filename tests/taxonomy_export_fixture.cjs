// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native original inputs and source-bound export observations.
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const {
  readCitations,
} = require("../04_interactive_presentation/scripts/taxonomy_citations.cjs");
const {
  readCatalogue,
  readHistoricalAudit,
} = require("../04_interactive_presentation/scripts/taxonomy_export_inputs.cjs");
const { loadFixture, getRequired } = require("./taxonomy_citation_fixture.cjs");
const root = path.resolve(__dirname, "..");
const input = "metadata/taxonomy_audit/claim_citations.json";
const originalBytes = fs.readFileSync(path.join(root, input));
const { original } = loadFixture(root);

/**
 * Native emitted audit document with complete original history and resolved claims.
 * @typedef {object} AuditDocument
 * @property {"1.3.0"} schema_version Original export schema.
 * @property {number} record_count Actual complete record count.
 * @property {(import("../04_interactive_presentation/scripts/taxonomy_export_inputs.cjs").HistoricalAudit & {
 * claim_citations: import("../04_interactive_presentation/scripts/taxonomy_citations.cjs").ResolvedCitation[],
 * complete_entry_review: false})[]} records Original history and current bounded claims.
 */

/**
 * Require an actual object before reading unknown JSON cells.
 * @param {unknown} value Native parsed wire cell.
 * @returns {Record<string, unknown>} Actual object whose individual cells remain unknown.
 * @throws {import("node:assert").AssertionError} The wire cell is not an object.
 */
function objectCell(value) {
  assert.ok(
    value !== null && typeof value === "object" && !Array.isArray(value),
  );
  return /** @type {Record<string, unknown>} */ (value);
}

/**
 * Retrieve original citation metadata only while candidate bytes remain unchanged.
 * The independent original fixture already passed owning production validation.
 * Candidate taxonomy may be intentionally damaged separately after copying.
 * @param {string} candidate Candidate containing the unchanged original metadata copy.
 * @returns {import("./taxonomy_citation_fixture.cjs").CitationDocument} Separate original metadata for deliberate mutations.
 * @throws {import("node:assert").AssertionError} Candidate metadata bytes are no longer original.
 */
function readOriginalCitations(candidate) {
  assert.deepEqual(fs.readFileSync(path.join(candidate, input)), originalBytes);
  return structuredClone(original);
}

/**
 * Read actual JSON output only after proving its complete bindings to original inputs.
 * Native citation validation supplies expected claims; original TSV parsing supplies
 * preserved historical columns. This compares the emitted product to its inputs,
 * rather than accepting unchecked JSON or deriving expectations from another output.
 * @param {string} candidate Actual candidate that completed public export.
 * @returns {AuditDocument} Actual emitted and source-bound audit product.
 * @throws {import("node:assert").AssertionError} A schema, identity, history or claim binding changed.
 */
function readAuditOutput(candidate) {
  /** @type {unknown} */
  const parsed = JSON.parse(
    fs.readFileSync(
      path.join(
        candidate,
        "04_interactive_presentation/data/taxonomy-audit.json",
      ),
      "utf8",
    ),
  );
  const document = objectCell(parsed);
  const citations = readCitations(candidate, readCatalogue(candidate));
  const historical = new Map(
    readHistoricalAudit(candidate).map((row) => [row.id, row]),
  );
  assert.equal(document.schema_version, "1.3.0");
  assert.equal(document.record_count, citations.size);
  assert.ok(Array.isArray(document.records));
  const records = /** @type {unknown[]} */ (document.records);
  assert.equal(records.length, citations.size);
  const ids = [...citations.keys()];
  for (const [index, member] of records.entries()) {
    const record = objectCell(member);
    assert.equal(record.id, ids[index]);
    assert.ok(typeof record.id === "string");
    assert.equal(record.complete_entry_review, false);
    assert.deepEqual(record.claim_citations, getRequired(citations, record.id));
    const { claim_citations, complete_entry_review, ...history } = record;
    assert.ok(Array.isArray(claim_citations));
    assert.equal(complete_entry_review, false);
    assert.deepEqual(history, getRequired(historical, record.id));
  }
  return /** @type {AuditDocument} */ (parsed);
}

/**
 * Execute the genuine exported classic script and compare its entire document.
 * @param {string} candidate Actual candidate containing the published JS product.
 * @param {AuditDocument} expected Independently source-bound JSON product.
 * @returns {AuditDocument} Actual script output after complete native equality.
 * @throws {import("node:assert").AssertionError} The JS and original JSON products differ.
 */
function readAuditScript(candidate, expected) {
  const host = { REACTOR_TAXONOMY_AUDIT: /** @type {unknown} */ (undefined) };
  vm.runInNewContext(
    fs.readFileSync(
      path.join(
        candidate,
        "04_interactive_presentation/data/taxonomy-audit.js",
      ),
      "utf8",
    ),
    { window: host },
  );
  const document = structuredClone(host.REACTOR_TAXONOMY_AUDIT);
  assert.deepEqual(document, expected);
  return /** @type {AuditDocument} */ (document);
}

module.exports = {
  objectCell,
  readOriginalCitations,
  readAuditOutput,
  readAuditScript,
};
