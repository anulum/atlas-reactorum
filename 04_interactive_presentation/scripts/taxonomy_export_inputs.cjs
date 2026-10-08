// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original taxonomy and historical audit input contracts.
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { isDeepStrictEqual } = require("node:util");
const construction = require("../taxonomy-construction.js");

/**
 * Complete original taxonomy row; numeric absence does not imply a score.
 * @typedef {object} TaxonomyRow
 * @property {string} id Stable identity.
 * @property {string} name Original display name.
 * @property {string} domain Original domain.
 * @property {string} family Original family.
 * @property {string} parent Original parent name or family.
 * @property {string|null} parent_id Linked parent identity or explicit absence.
 * @property {string} kind Original entity classification.
 * @property {string} maturity Original maturity description.
 * @property {string} evidence Original evidence classification.
 * @property {string} principle Complete physical principle.
 * @property {string} strength Complete strength statement.
 * @property {string} challenge Complete challenge statement.
 * @property {string} temp Original temperature context.
 * @property {string} mode Original operation context.
 * @property {number|null} scale Original scalar or explicit absence.
 * @property {number|null} control Original scalar or explicit absence.
 * @property {string[]} source_ids Original reference identities.
 * @property {string[]} source_urls Original reference URLs.
 * @property {string} evidence_scope Exact scope of the evidence.
 * @property {string} reviewed_on Original review date.
 * @property {string} source_audit Original source-audit wording.
 */

/**
 * Minimally checked catalogue identity; other cells remain unknown before binding.
 * @typedef {Record<string, unknown> & {
 * id: string, source_urls: string[], parent_id: string|null
 * }} CatalogueInput
 */

/**
 * Original historical audit columns, preserved separately from current claims.
 * @typedef {object} HistoricalAudit
 * @property {string} id Original entry identity.
 * @property {string} name Original audited name.
 * @property {string} classification_ok Historical classification disposition.
 * @property {string} source_directness Historical source-support description.
 * @property {string} source_access Historical access observation.
 * @property {string} issue Original historical question.
 * @property {string} recommended_action Original recommended review action.
 * @property {string} verified_source_url Historical locator, including explicit empty cells.
 * @property {string} audit_date Original historical date.
 */

const AUDIT_FIELDS = [
  "id",
  "name",
  "classification_ok",
  "source_directness",
  "source_access",
  "issue",
  "recommended_action",
  "verified_source_url",
  "audit_date",
];
const TEXT_FIELDS = [
  "id",
  "name",
  "domain",
  "family",
  "parent",
  "kind",
  "maturity",
  "evidence",
  "principle",
  "strength",
  "challenge",
  "temp",
  "mode",
  "evidence_scope",
  "reviewed_on",
  "source_audit",
];

/**
 * Load the original classic script and check identities before citation binding.
 * The VM host is the original data-script boundary, not a browser window.
 * Native structured cloning restores local prototypes while retaining authored
 * non-finite values for refusal instead of normalising them into missing cells.
 * @param {string} repositoryRoot Complete candidate repository.
 * @returns {CatalogueInput[]} Original rows with checked identity and reference cells.
 * @throws {Error} A collection, identity, reference or parent is invalid.
 */
function readCatalogue(repositoryRoot) {
  const host = { REACTOR_TAXONOMY: /** @type {unknown} */ (undefined) };
  vm.runInNewContext(
    fs.readFileSync(
      path.join(
        repositoryRoot,
        "04_interactive_presentation/data/taxonomy-expanded.js",
      ),
      "utf8",
    ),
    { window: host, AtlasTaxonomyConstruction: construction },
    {
      filename: path.join(
        repositoryRoot,
        "04_interactive_presentation/data/taxonomy-expanded.js",
      ),
    },
  );
  /** @type {unknown} */
  const parsed = structuredClone(host.REACTOR_TAXONOMY);
  if (!Array.isArray(parsed))
    throw new Error("Taxonomy catalogue must be an array");
  const rows = /** @type {unknown[]} */ (parsed);
  /** @type {Set<string>} */
  const ids = new Set();
  /** @type {CatalogueInput[]} */
  const checked = [];
  for (const entry of rows) {
    if (entry === null || typeof entry !== "object" || Array.isArray(entry))
      throw new Error("Taxonomy entry must be an object");
    const row = /** @type {Record<string, unknown>} */ (entry);
    if (typeof row.id !== "string" || !row.id)
      throw new Error("Taxonomy entry must have a string identity");
    if (ids.has(row.id)) throw new Error(`Duplicate ID: ${row.id}`);
    ids.add(row.id);
    if (!Array.isArray(row.source_urls))
      throw new Error(`Invalid sources: ${row.name}`);
    const urls = /** @type {unknown[]} */ (row.source_urls);
    if (
      urls.length === 0 ||
      urls.some((url) => typeof url !== "string" || !/^https:\/\//.test(url))
    )
      throw new Error(`Invalid sources: ${row.name}`);
    if (row.parent_id !== null && typeof row.parent_id !== "string")
      throw new Error(`Invalid parent: ${row.id}`);
    checked.push(/** @type {CatalogueInput} */ (row));
  }
  for (const row of checked) {
    if (row.parent_id && !ids.has(row.parent_id))
      throw new Error(`Missing parent: ${row.id}`);
  }
  return checked;
}

/**
 * Finish complete row shape checking after the owning citation validation.
 * Citation binding runs first to preserve its specific physical-field refusals.
 * This checks cell types; the native evidence-profile validator owns their
 * source-bound scientific and context meanings before publication.
 * @param {readonly CatalogueInput[]} rows Actual catalogue rows already citation-bound.
 * @returns {TaxonomyRow[]} Complete original row shapes without rewriting cells.
 * @throws {Error} An original text, reference list or scalar cell is malformed.
 */
function completeCatalogue(rows) {
  /** @type {TaxonomyRow[]} */
  const complete = [];
  for (const row of rows) {
    for (const field of TEXT_FIELDS) {
      if (typeof row[field] !== "string")
        throw new Error(`Taxonomy ${field} must be text`);
    }
    for (const field of ["scale", "control"]) {
      if (
        row[field] !== null &&
        (typeof row[field] !== "number" || !Number.isFinite(row[field]))
      )
        throw new Error(`Taxonomy ${field} must be a finite scalar or null`);
    }
    if (!Array.isArray(row.source_ids))
      throw new Error("Taxonomy source identities must be a text array");
    const sourceIds = /** @type {unknown[]} */ (row.source_ids);
    if (sourceIds.some((value) => typeof value !== "string"))
      throw new Error("Taxonomy source identities must be a text array");
    complete.push(/** @type {TaxonomyRow} */ (row));
  }
  return complete;
}

/**
 * Read all original historical TSV columns without changing empty cells.
 * Missing audit input retains the original empty-audit path; the complete
 * native evidence-profile validator subsequently refuses unsupported snapshots.
 * @param {string} repositoryRoot Complete candidate repository.
 * @returns {HistoricalAudit[]} Original historical records in their original order.
 * @throws {Error} The present audit has changed columns.
 */
function readHistoricalAudit(repositoryRoot) {
  const filename = path.join(
    repositoryRoot,
    "metadata/taxonomy_audit/audit.tsv",
  );
  if (!fs.existsSync(filename)) return [];
  const [header, ...lines] = fs
    .readFileSync(filename, "utf8")
    .trimEnd()
    .split(/\r?\n/)
    .map((line) => line.split("\t"));
  if (!isDeepStrictEqual(header, AUDIT_FIELDS))
    throw new Error(
      "Taxonomy audit columns differ from the historical contract",
    );
  return lines.map(
    (values) =>
      /** @type {HistoricalAudit} */ (
        Object.fromEntries(
          header.map((key, index) => [key, values[index] || ""]),
        )
      ),
  );
}

module.exports = { readCatalogue, completeCatalogue, readHistoricalAudit };
