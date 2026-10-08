// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — 04_interactive_presentation/scripts/export_taxonomy.cjs

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const {
  readCatalogue,
  completeCatalogue,
  readHistoricalAudit,
} = require("./taxonomy_export_inputs.cjs");
const { publishProducts } = require("./taxonomy_export_products.cjs");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { readCitations } = require("./taxonomy_citations.cjs");

/**
 * Native complete export counts; domain values count actual original rows.
 * @typedef {{entries: number, audited: number, domains: Record<string, number>}} ExportSummary
 */

/**
 * Rebuild all five taxonomy products from one complete, source-bound candidate.
 * Input checks finish before any product is written. Historical audit fields are
 * preserved; partial citations never establish complete scientific review.
 * @param {string} repositoryRoot Candidate root, including taxonomy and audit metadata.
 * @returns {ExportSummary} Entry, historical audit and per-domain counts.
 * @throws {Error} When catalogue identities, references or citations are invalid.
 */
function exportTaxonomy(repositoryRoot) {
  const root = path.join(repositoryRoot, "04_interactive_presentation");
  const catalogue = readCatalogue(repositoryRoot);
  const audits = readHistoricalAudit(repositoryRoot);
  /** @type {Record<string, import("./taxonomy_export_inputs.cjs").HistoricalAudit>} */
  const auditById = Object.fromEntries(audits.map((row) => [row.id, row]));
  const citationById = readCitations(repositoryRoot, catalogue);
  const rows = completeCatalogue(catalogue);
  const ids = new Set(rows.map((row) => row.id));
  /** @type {readonly (keyof import("./taxonomy_export_inputs.cjs").TaxonomyRow | "claim_citations")[]} */
  const fields = [
    "id",
    "name",
    "domain",
    "family",
    "parent_id",
    "kind",
    "maturity",
    "evidence",
    "evidence_scope",
    "source_urls",
    "source_audit",
    "claim_citations",
  ];
  /**
   * Serialize an original TSV cell without embedded row or column delimiters.
   * @param {string|number|null|string[]} value Original row cell or serialized citations.
   * @returns {string} Original export cell representation.
   */
  const cell = (value) =>
    (Array.isArray(value) ? value.join(" | ") : String(value ?? "")).replace(
      /[\t\r\n]/g,
      " ",
    );
  const exportedRows = Array.from(citationById, ([id, citations], index) => {
    const row = rows[index];
    return {
      ...row,
      source_audit: auditById[id]
        ? `${auditById[id].classification_ok}; ${auditById[id].source_directness}`
        : row.source_audit,
      claim_citations: JSON.stringify(citations),
    };
  });
  const auditRecords = Array.from(citationById, ([id, citations], index) => {
    const row = rows[index];
    return {
      ...(auditById[id] || {
        id: row.id,
        name: row.name,
        classification_ok: "not-yet-audited",
        source_directness:
          "introductory reference mapping; per-claim verification pending",
        source_access: "",
        issue: "This entry was added after the first taxonomy audit.",
        recommended_action:
          "Complete entry-level classification and source review.",
        verified_source_url: "",
        audit_date: "",
      }),
      claim_citations: citations,
      complete_entry_review: false,
    };
  });
  const auditDocument = {
    schema_version: "1.3.0",
    record_count: auditRecords.length,
    records: auditRecords,
  };
  const serializedAudit = JSON.stringify(auditDocument, null, 2) + "\n";
  const serializedTsv =
    [
      fields.join("\t"),
      ...exportedRows.map((row) =>
        fields.map((field) => cell(row[field])).join("\t"),
      ),
    ].join("\n") + "\n";
  const snapshot = createHash("sha256")
    .update(fs.readFileSync(path.join(root, "data/taxonomy-expanded.js")))
    .digest("hex");
  const validated = spawnSync(
    process.env.ATLAS_PYTHON || "python3",
    [
      path.resolve(__dirname, "../../metadata/evidence_profiles/validate.py"),
      "--root",
      repositoryRoot,
      "--snapshot",
      snapshot,
    ],
    { encoding: "utf8", timeout: 45000, maxBuffer: 8 * 1024 * 1024 },
  );
  if (validated.status !== 0)
    throw new Error("Evidence profiles: complete snapshot validation failed");
  /** @type {unknown} */
  const profileDocument = JSON.parse(validated.stdout);
  const serializedProfiles = JSON.stringify(profileDocument, null, 2) + "\n";
  const products = new Map([
    ["taxonomy-expanded.sources.tsv", serializedTsv],
    ["taxonomy-audit.json", serializedAudit],
    [
      "taxonomy-audit.js",
      `window.REACTOR_TAXONOMY_AUDIT = ${serializedAudit.trimEnd()};\n`,
    ],
    ["taxonomy-evidence-profiles.json", serializedProfiles],
    [
      "taxonomy-evidence-profiles.js",
      `window.REACTOR_TAXONOMY_EVIDENCE_PROFILES = ${serializedProfiles.trimEnd()};\n`,
    ],
  ]);
  publishProducts(path.join(root, "data"), products);
  /** @type {Record<string, number>} */
  const domains = {};
  for (const row of rows) domains[row.domain] = (domains[row.domain] || 0) + 1;
  return {
    entries: rows.length,
    audited: audits.filter((row) => ids.has(row.id)).length,
    domains,
  };
}

module.exports = { exportTaxonomy };
if (require.main === module) {
  if (
    process.argv.length !== 2 &&
    (process.argv.length !== 4 || process.argv[2] !== "--root")
  )
    throw new Error("Usage: export_taxonomy.cjs [--root REPOSITORY]");
  const repositoryRoot =
    process.argv.length === 4
      ? path.resolve(process.argv[3])
      : path.resolve(__dirname, "../..");
  console.log(JSON.stringify(exportTaxonomy(repositoryRoot)));
}
