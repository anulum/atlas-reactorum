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
const vm = require("node:vm");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { readCitations } = require("./taxonomy_citations.cjs");

/**
 * Rebuild all five taxonomy products from one complete, source-bound candidate.
 *
 * @param {string} repositoryRoot Candidate root, including taxonomy and audit metadata.
 * @returns {object} Entry, historical audit and per-domain counts.
 * @throws {Error} When catalogue identities, references or citations are invalid.
 *
 * Input checks finish before any product is written. Historical audit fields are
 * preserved; partial citations never establish complete scientific review.
 */
function exportTaxonomy(repositoryRoot) {
  const root = path.join(repositoryRoot, "04_interactive_presentation");
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.join(root, "data/taxonomy-expanded.js"), "utf8"), { window });
  const rows = JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY));
  const auditPath = path.join(repositoryRoot, "metadata/taxonomy_audit/audit.tsv");
  const parseTsv = text => {
    const [header, ...lines] = text.trimEnd().split(/\r?\n/).map(line => line.split("\t"));
    return lines.map(values => Object.fromEntries(header.map((key, index) => [key, values[index] || ""])));
  };
  const audits = fs.existsSync(auditPath) ? parseTsv(fs.readFileSync(auditPath, "utf8")) : [];
  const auditById = Object.fromEntries(audits.map(row => [row.id, row]));
  const ids = new Set();
  for (const row of rows) {
    if (ids.has(row.id)) throw new Error(`Duplicate ID: ${row.id}`);
    ids.add(row.id);
    if (!row.source_urls.length || row.source_urls.some(url => !/^https:\/\//.test(url))) throw new Error(`Invalid sources: ${row.name}`);
  }
  for (const row of rows) {
    if (row.parent_id && !ids.has(row.parent_id)) throw new Error(`Missing parent: ${row.id}`);
  }
  const citationById = readCitations(repositoryRoot, rows);
  const fields = ["id", "name", "domain", "family", "parent_id", "kind", "maturity", "evidence", "evidence_scope", "source_urls", "source_audit", "claim_citations"];
  const cell = value => (Array.isArray(value) ? value.join(" | ") : String(value ?? "")).replace(/[\t\r\n]/g, " ");
  const exportedRows = rows.map(row => ({
    ...row,
    source_audit: auditById[row.id]
      ? `${auditById[row.id].classification_ok}; ${auditById[row.id].source_directness}`
      : row.source_audit,
    claim_citations: JSON.stringify(citationById.get(row.id)),
  }));
  const auditRecords = rows.map(row => ({
    ...(auditById[row.id] || {
      id: row.id,
      name: row.name,
      classification_ok: "not-yet-audited",
      source_directness: "introductory reference mapping; per-claim verification pending",
      source_access: "",
      issue: "This entry was added after the first taxonomy audit.",
      recommended_action: "Complete entry-level classification and source review.",
      verified_source_url: "",
      audit_date: "",
    }),
    claim_citations: citationById.get(row.id),
    complete_entry_review: false,
  }));
  const auditDocument = { schema_version: "1.3.0", record_count: auditRecords.length, records: auditRecords };
  const serializedAudit = JSON.stringify(auditDocument, null, 2) + "\n";
  const serializedTsv = [fields.join("\t"), ...exportedRows.map(row => fields.map(field => cell(row[field])).join("\t"))].join("\n") + "\n";
  const snapshot = createHash("sha256").update(fs.readFileSync(path.join(root, "data/taxonomy-expanded.js"))).digest("hex");
  const validated = spawnSync(process.env.ATLAS_PYTHON || "python3", [
    path.resolve(__dirname, "../../metadata/evidence_profiles/validate.py"),
    "--root", repositoryRoot, "--snapshot", snapshot,
  ], { encoding: "utf8", timeout: 45000, maxBuffer: 8 * 1024 * 1024 });
  if (validated.status !== 0) throw new Error("Evidence profiles: complete snapshot validation failed");
  const serializedProfiles = JSON.stringify(JSON.parse(validated.stdout), null, 2) + "\n";
  const products = new Map([
    ["taxonomy-expanded.sources.tsv", serializedTsv],
    ["taxonomy-audit.json", serializedAudit],
    ["taxonomy-audit.js", `window.REACTOR_TAXONOMY_AUDIT = ${serializedAudit.trimEnd()};\n`],
    ["taxonomy-evidence-profiles.json", serializedProfiles],
    ["taxonomy-evidence-profiles.js", `window.REACTOR_TAXONOMY_EVIDENCE_PROFILES = ${serializedProfiles.trimEnd()};\n`],
  ]);
  // Prepare the complete set before publishing any member. Roll back replaced
  // members on an I/O failure; invalid inputs never reach this transaction.
  const dataRoot = path.join(root, "data");
  const stage = fs.mkdtempSync(path.join(dataRoot, ".taxonomy-build-"));
  const originals = new Map();
  const published = [];
  try {
    for (const [name, content] of products) {
      fs.writeFileSync(path.join(stage, name), content);
    }
    for (const name of products.keys()) {
      const target = path.join(dataRoot, name);
      originals.set(name, fs.existsSync(target) ? fs.readFileSync(target) : null);
      fs.renameSync(path.join(stage, name), target);
      published.push(name);
    }
  } catch (error) {
    for (const name of published.reverse()) {
      const target = path.join(dataRoot, name);
      const original = originals.get(name);
      if (original === null) fs.unlinkSync(target);
      else fs.writeFileSync(target, original);
    }
    throw error;
  } finally {
    fs.rmSync(stage, { recursive: true });
  }
  return {
    entries: rows.length,
    audited: audits.filter(row => ids.has(row.id)).length,
    domains: rows.reduce((out, row) => { out[row.domain] = (out[row.domain] || 0) + 1; return out; }, {}),
  };
}

module.exports = { exportTaxonomy };
if (require.main === module) {
  if (process.argv.length !== 2 && (process.argv.length !== 4 || process.argv[2] !== "--root")) throw new Error("Usage: export_taxonomy.cjs [--root REPOSITORY]");
  const repositoryRoot = process.argv.length === 4 ? path.resolve(process.argv[3]) : path.resolve(__dirname, "../..");
  console.log(JSON.stringify(exportTaxonomy(repositoryRoot)));
}
