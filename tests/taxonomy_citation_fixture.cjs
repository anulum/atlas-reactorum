// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual citation fixtures and asserted test lookups.
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");
const os = require("node:os");
const construction = require("../04_interactive_presentation/taxonomy-construction.js");
const {
  readCitations,
} = require("../04_interactive_presentation/scripts/taxonomy_citations.cjs");

/**
 * Complete physical fields bound by the owning citation validator.
 * @typedef {object} BoundValues
 * @property {string} name Original entry name.
 * @property {string} kind Original classification kind.
 * @property {string} family Original reactor family.
 * @property {string} principle Complete physical principle.
 * @property {string} strength Complete strength statement.
 * @property {string} challenge Complete challenge statement.
 * @property {string} maturity Original maturity classification.
 * @property {string} evidence Original evidence classification.
 * @property {string[]} source_urls Original source locators.
 */

/**
 * Actual catalogue row, including independently checked lineage and review cells.
 * @typedef {BoundValues & {id: string, parent_id: string|null,
 * reviewed_on: string, evidence_scope: string}} TaxonomyEntry
 */

/**
 * Complete original citation metadata after the production validator succeeds.
 * @typedef {object} CitationDocument
 * @property {"1.2.0"} schema_version Owning metadata schema.
 * @property {string} taxonomy_sha256 Actual classic-script source digest.
 * @property {import("../04_interactive_presentation/scripts/taxonomy_citations.cjs").CitationSource[]} sources Original source records.
 * @property {{id: string, values: BoundValues, complete_entry_review: false,
 * citations: import("../04_interactive_presentation/scripts/taxonomy_citations.cjs").Citation[]}[]} records Original claim records.
 */

/**
 * Load the unchanged actual classic script and validate its complete metadata.
 * The production reader checks bound values, source custody and every claim.
 * Byte readback ties the parsed fixture to that checked file. The minimal VM
 * host loads the original data script; it does not represent a browser window.
 * Structured cloning restores native array prototypes before deep value checks.
 * @param {string} root Actual repository containing both original inputs.
 * @returns {{rows: TaxonomyEntry[], original: CitationDocument}} Validated original fixtures.
 * @throws {Error} Original inputs fail production validation or fixture checks.
 */
function loadFixture(root) {
  const metadataPath = path.join(
    root,
    "metadata/taxonomy_audit/claim_citations.json",
  );
  const taxonomyPath = path.join(
    root,
    "04_interactive_presentation/data/taxonomy-expanded.js",
  );
  const metadataBytes = fs.readFileSync(metadataPath);
  const taxonomyBytes = fs.readFileSync(taxonomyPath);
  /** @type {unknown} */
  const document = JSON.parse(metadataBytes.toString("utf8"));
  const host = { REACTOR_TAXONOMY: /** @type {unknown} */ (undefined) };
  vm.runInNewContext(
    taxonomyBytes.toString("utf8"),
    { window: host, AtlasTaxonomyConstruction: construction },
    { filename: taxonomyPath },
  );
  const candidateRows = structuredClone(host.REACTOR_TAXONOMY);
  readCitations(root, candidateRows);
  assert.deepEqual(
    fs.readFileSync(metadataPath),
    metadataBytes,
    "Validated metadata bytes changed during loading",
  );
  assert.deepEqual(
    fs.readFileSync(taxonomyPath),
    taxonomyBytes,
    "Validated taxonomy bytes changed during loading",
  );
  assert.ok(Array.isArray(candidateRows));
  const entries = /** @type {unknown[]} */ (candidateRows);
  for (const entry of entries) {
    assert.ok(
      entry !== null && typeof entry === "object" && !Array.isArray(entry),
    );
    const row = /** @type {Record<string, unknown>} */ (entry);
    assert.equal(typeof row.reviewed_on, "string");
    assert.equal(typeof row.evidence_scope, "string");
    assert.ok(row.parent_id === null || typeof row.parent_id === "string");
  }
  return {
    rows: /** @type {TaxonomyEntry[]} */ (candidateRows),
    original: /** @type {CitationDocument} */ (document),
  };
}

/**
 * Assert that an actual collection contains the expected original member.
 * @template T
 * @param {readonly T[]} collection Actual rows, sources or claims.
 * @param {(value: T) => boolean} predicate Original member selection.
 * @returns {T} Existing member, with no invented fallback.
 * @throws {import("node:assert").AssertionError} The selected member is absent.
 */
function findRequired(collection, predicate) {
  const found = collection.find(predicate);
  assert.ok(found !== undefined, "Expected original fixture member is absent");
  return found;
}

/**
 * Require an existing identity in an actual source-result or parsed-text map.
 * @template V
 * @param {Map<string, V>} resolved Owning result or parsed-text identity map.
 * @param {string} id Expected original identity.
 * @returns {V} Existing value, with no invented fallback.
 * @throws {import("node:assert").AssertionError} The original identity was not resolved.
 */
function getRequired(resolved, id) {
  const found = resolved.get(id);
  assert.ok(found !== undefined, "Expected resolved identity is absent: " + id);
  return found;
}

/**
 * Select a complete physical field only after checking its actual topic.
 * @param {BoundValues} row Original physical values.
 * @param {string} topic Actual resolved citation topic.
 * @returns {string} Original complete physical statement.
 * @throws {import("node:assert").AssertionError} The topic is not a physical field.
 */
function physicalField(row, topic) {
  assert.ok(
    topic === "principle" || topic === "strength" || topic === "challenge",
  );
  return row[topic];
}

/**
 * A deliberate mutation of complete actual metadata and its expected refusal.
 * @typedef {[string, (document: CitationDocument) => unknown, RegExp]} DamageCase
 */

/**
 * Register metadata refusals against isolated copies of both original inputs.
 * Wrong wire values enter through native mutation operations, without declaring
 * that damaged objects satisfy the valid schema. The reader must reject them
 * without rewriting the submitted original bytes.
 * @param {readonly DamageCase[]} cases Deliberate input faults and original refusal patterns.
 * @returns {void} Registers the complete owning rejection cases with Node test.
 */
function runDamageCases(cases) {
  const root = path.resolve(__dirname, "..");
  const input = "metadata/taxonomy_audit/claim_citations.json";
  const taxonomy = "04_interactive_presentation/data/taxonomy-expanded.js";
  const { rows, original } = loadFixture(root);
  for (const [label, change, expected] of cases) {
    test(`refuse ${label} in the complete actual metadata`, (context) => {
      const dir = fs.mkdtempSync(
        path.join(
          process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(),
          "atlas-citations-",
        ),
      );
      context.after(() => fs.rmSync(dir, { recursive: true }));
      for (const relative of [input, taxonomy]) {
        const target = path.join(dir, relative);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.copyFileSync(path.join(root, relative), target);
      }
      const damaged = structuredClone(original);
      /** @type {unknown} */
      let document = damaged;
      const replacement = change(damaged);
      if (replacement !== undefined) document = replacement;
      fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
      const before = fs.readFileSync(path.join(dir, input));
      assert.throws(() => readCitations(dir, rows), expected);
      assert.deepEqual(fs.readFileSync(path.join(dir, input)), before);
    });
  }
}

module.exports = {
  loadFixture,
  findRequired,
  getRequired,
  physicalField,
  runDamageCases,
};
