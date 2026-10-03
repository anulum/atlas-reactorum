// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native full-catalogue taxonomy export conformance
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const { createHash } = require("node:crypto");
const { spawnSync } = require("node:child_process");
const { exportTaxonomy } = require("../04_interactive_presentation/scripts/export_taxonomy.cjs");
const root = path.resolve(__dirname, "..");
const script = path.join(root, "04_interactive_presentation/scripts/export_taxonomy.cjs");
const data = "04_interactive_presentation/data";
const input = "metadata/taxonomy_audit/claim_citations.json";
const audit = "metadata/taxonomy_audit/audit.tsv";
const outputs = ["taxonomy-expanded.sources.tsv", "taxonomy-audit.json", "taxonomy-audit.js"];

function candidate(context) {
  const dir = fs.mkdtempSync(path.join(process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(), "atlas-taxonomy-export-"));
  context.after(() => fs.rmSync(dir, { recursive: true }));
  for (const relative of [input, audit, `${data}/taxonomy-expanded.js`, ...outputs.map(name => `${data}/${name}`)]) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, relative), target);
  }
  return dir;
}

function productBytes(dir) {
  return outputs.map(name => fs.readFileSync(path.join(dir, data, name)));
}

test("public export preserves all 135 historical audit rows and supplies identical citations in TSV, JSON and JS", context => {
  const dir = candidate(context);
  const auditBefore = fs.readFileSync(path.join(dir, audit));
  const taxonomyBefore = fs.readFileSync(path.join(dir, data, "taxonomy-expanded.js"));
  assert.deepEqual(exportTaxonomy(dir), { entries: 135, audited: 135, domains: { fission: 29, fusion: 32, chemical: 52, hybrid: 22 } });
  const document = JSON.parse(fs.readFileSync(path.join(dir, data, "taxonomy-audit.json"), "utf8"));
  assert.equal(document.schema_version, "1.3.0");
  assert.equal(document.record_count, 135);
  assert.equal(document.records.length, 135);
  const [header, ...lines] = auditBefore.toString().trimEnd().split("\n").map(line => line.split("\t"));
  const originalById = new Map(lines.map(values => [values[0], Object.fromEntries(header.map((field, i) => [field, values[i]]))]));
  for (const record of document.records) {
    const { claim_citations, complete_entry_review, ...historical } = record;
    assert.deepEqual(historical, originalById.get(record.id));
    assert.equal(complete_entry_review, false);
    assert.ok(Array.isArray(claim_citations));
  }
  assert.equal(document.records.flatMap(record => record.claim_citations).length, 599);
  const retained = document.records.flatMap(record => record.claim_citations).filter(citation => citation.source_capture_method === "retained-source-review");
  assert.equal(retained.length, 177);
  assert.ok(retained.every(citation => citation.source_captured_at === null));
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.join(dir, data, "taxonomy-audit.js"), "utf8"), { window });
  assert.deepEqual(JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY_AUDIT)), document);
  const [fields, ...tsv] = fs.readFileSync(path.join(dir, data, "taxonomy-expanded.sources.tsv"), "utf8").trimEnd().split("\n").map(line => line.split("\t"));
  assert.equal(tsv.length, 135);
  for (const [index, row] of tsv.entries()) {
    assert.equal(row[0], document.records[index].id);
    assert.deepEqual(JSON.parse(row[fields.indexOf("claim_citations")]), document.records[index].claim_citations);
  }
  assert.deepEqual(fs.readFileSync(path.join(dir, audit)), auditBefore);
  assert.deepEqual(fs.readFileSync(path.join(dir, data, "taxonomy-expanded.js")), taxonomyBefore);
  const first = productBytes(dir);
  exportTaxonomy(dir);
  assert.deepEqual(productBytes(dir), first);
});

test("segmented flow exports as a configuration with no required microchannel parent", context => {
  const dir = candidate(context);
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const [fields, ...records] = fs.readFileSync(path.join(dir, data, "taxonomy-expanded.sources.tsv"), "utf8")
    .trimEnd().split("\n").map(line => line.split("\t"));
  const values = records.find(row => row[fields.indexOf("id")] === "segmented-flow-reactor");
  const row = Object.fromEntries(fields.map((field, index) => [field, values[index]]));
  assert.equal(row.kind, "configuration");
  assert.equal(row.parent_id, "");
  assert.equal(row.maturity, "demonstrated");
  assert.equal(row.evidence, "demonstrated");
  const claims = JSON.parse(row.claim_citations);
  const classification = claims.find(claim => claim.topic === "classification");
  assert.match(classification.scope, /3 mm flow tube/);
  assert.match(classification.source_url, /PMC13159419/);
  assert.deepEqual([...new Set(claims.filter(claim => claim.topic !== "classification").map(claim => claim.topic))],
    ["principle", "strength", "challenge"]);
  const audited = JSON.parse(fs.readFileSync(path.join(dir, data, "taxonomy-audit.json"), "utf8"))
    .records.find(record => record.id === "segmented-flow-reactor");
  assert.equal(audited.complete_entry_review, false);
  assert.match(audited.recommended_action, /configuration/);
});

test("native CLI resolves an explicit candidate from another directory and refuses malformed arguments", context => {
  const dir = candidate(context);
  const result = spawnSync(process.execPath, [script, "--root", dir], { cwd: os.tmpdir(), encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(JSON.parse(result.stdout).entries, 135);
  const first = productBytes(dir);
  for (const args of [["--unknown"], ["--other", dir], ["--root", dir, "extra"]]) {
    const refused = spawnSync(process.execPath, [script, ...args], { encoding: "utf8", timeout: 15000 });
    assert.equal(refused.status, 1);
    assert.match(refused.stderr, /Usage: export_taxonomy/);
    assert.deepEqual(productBytes(dir), first);
  }
});

test("native default CLI reproduces the canonical products from another working directory", () => {
  const before = productBytes(root);
  const result = spawnSync(process.execPath, [script], { cwd: os.tmpdir(), encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(JSON.parse(result.stdout).audited, 135);
  assert.deepEqual(productBytes(root), before);
});

test("missing historical audit stays unaudited without manufacturing whole-entry approval", context => {
  const dir = candidate(context);
  fs.unlinkSync(path.join(dir, audit));
  assert.equal(exportTaxonomy(dir).audited, 0);
  const document = JSON.parse(fs.readFileSync(path.join(dir, data, "taxonomy-audit.json"), "utf8"));
  assert.equal(document.records.length, 135);
  assert.ok(document.records.every(row => row.classification_ok === "not-yet-audited" && row.complete_entry_review === false));
  assert.equal(document.records.flatMap(row => row.claim_citations).length, 599);
});

for (const [label, appended, expected] of [
  ["duplicate identity", "window.REACTOR_TAXONOMY.push(window.REACTOR_TAXONOMY[0]);", /Duplicate ID/],
  ["empty sources", "window.REACTOR_TAXONOMY[0].source_urls=[];", /Invalid sources/],
  ["bad source scheme", "window.REACTOR_TAXONOMY[0].source_urls[0]='http://example.org/source';", /Invalid sources/],
  ["unknown parent", "window.REACTOR_TAXONOMY[0].parent_id='not-a-real-parent';", /Missing parent/],
  ["taxonomy hash drift", "\n", /stale taxonomy hash/],
]) {
  test(`refuse ${label} before changing any existing export`, context => {
    const dir = candidate(context);
    fs.appendFileSync(path.join(dir, data, "taxonomy-expanded.js"), appended);
    const before = productBytes(dir);
    assert.throws(() => exportTaxonomy(dir), expected);
    assert.deepEqual(productBytes(dir), before);
  });
}

test("mixed semantic catalogue and citation records fail even with an updated input hash", context => {
  const dir = candidate(context);
  const file = path.join(dir, data, "taxonomy-expanded.js");
  fs.appendFileSync(file, "window.REACTOR_TAXONOMY[0].principle += ' changed';");
  const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
  document.taxonomy_sha256 = createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
  const before = productBytes(dir);
  assert.throws(() => exportTaxonomy(dir), /changed taxonomy values/);
  assert.deepEqual(productBytes(dir), before);
});

test("incomplete citation input fails through the native CLI without rewriting products", context => {
  const dir = candidate(context);
  fs.unlinkSync(path.join(dir, input));
  const before = productBytes(dir);
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 1);
  assert.deepEqual(productBytes(dir), before);
});

test("updating both taxonomy hash and bound values cannot silently change a source-inspected physical statement", context => {
  const dir = candidate(context);
  const file = path.join(dir, data, "taxonomy-expanded.js");
  fs.appendFileSync(file, "window.REACTOR_TAXONOMY[0].principle = 'Heat transfer without pressure or a secondary circuit.';");
  const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
  document.taxonomy_sha256 = createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  document.records[0].values.principle = "Heat transfer without pressure or a secondary circuit.";
  fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
  const before = productBytes(dir);
  assert.throws(() => exportTaxonomy(dir), /complete physical field/);
  assert.deepEqual(productBytes(dir), before);
});

test("the native CLI refuses an invented original NRC capture timestamp before rewriting any product", context => {
  const dir = candidate(context);
  const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
  document.sources.find(source => source.id === "nrc-r100").captured_at = "2026-10-01T05:00:00Z";
  fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
  const before = productBytes(dir);
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /original capture time is unknown/);
  assert.deepEqual(productBytes(dir), before);
});

test("an updated hash and bound challenge cannot leave a stale lead-coolant source statement through the native CLI", context => {
  const dir = candidate(context);
  const file = path.join(dir, data, "taxonomy-expanded.js");
  const changed = "Corrosion has been completely eliminated in every lead-cooled reactor.";
  fs.appendFileSync(file, `window.REACTOR_TAXONOMY.find(row => row.id === 'lead-fast-reactor').challenge = ${JSON.stringify(changed)};`);
  const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
  document.taxonomy_sha256 = createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  document.records.find(record => record.id === "lead-fast-reactor").values.challenge = changed;
  fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
  const before = productBytes(dir);
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /complete physical field/);
  assert.deepEqual(productBytes(dir), before);
});

for (const [label, field, value, expected] of [
  ["an object-valued taxonomy kind", "kind", {}, /Bound taxonomy kind: expected nonempty single-line text/],
  ["a physical citation omitted from entry references", "source_urls", null, /Citation: physical source absent from entry references/],
]) {
  test(`the native CLI refuses ${label} even with matching hash and bound values`, context => {
    const dir = candidate(context);
    const file = path.join(dir, data, "taxonomy-expanded.js");
    const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
    const record = document.records.find(item => item.id === "pem-water-electrolyser");
    const changed = field === "source_urls" ? record.values.source_urls.filter(url => !url.endsWith("hydrogen-production-electrolysis")) : value;
    fs.appendFileSync(file, `window.REACTOR_TAXONOMY.find(row => row.id === 'pem-water-electrolyser')[${JSON.stringify(field)}] = ${JSON.stringify(changed)};`);
    document.taxonomy_sha256 = createHash("sha256").update(fs.readFileSync(file)).digest("hex");
    record.values[field] = changed;
    fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
    const before = productBytes(dir);
    const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
    assert.equal(result.status, 1);
    assert.match(result.stderr, expected);
    assert.deepEqual(productBytes(dir), before);
  });
}

test("native CLI exports the genuine XML section citations identically into every product", context => {
  const dir = candidate(context);
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const document = JSON.parse(fs.readFileSync(path.join(dir, data, "taxonomy-audit.json"), "utf8"));
  const record = document.records.find(row => row.id === "electrochemically-loaded-beam-target-fusion");
  assert.equal(record.complete_entry_review, false);
  assert.equal(record.claim_citations.length, 4);
  assert.ok(record.claim_citations.every(claim => claim.source_url.endsWith("/PMC12367529/fullTextXML") && claim.pdf_pages.length === 0 && claim.printed_pages.length === 0));
  assert.match(record.claim_citations.find(claim => claim.topic === "challenge").section, /Conclusion \(Sec5\)/);
  const [fields, ...tsv] = fs.readFileSync(path.join(dir, data, "taxonomy-expanded.sources.tsv"), "utf8").trimEnd().split("\n").map(line => line.split("\t"));
  const row = tsv.find(values => values[0] === record.id);
  assert.deepEqual(JSON.parse(row[fields.indexOf("claim_citations")]), record.claim_citations);
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.join(dir, data, "taxonomy-audit.js"), "utf8"), { window });
  assert.deepEqual(JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY_AUDIT)).records.find(row => row.id === record.id).claim_citations, record.claim_citations);
});

test("a valid full-catalogue export with one pending source review renders an honest uncited detail", context => {
  const dir = candidate(context);
  const document = JSON.parse(fs.readFileSync(path.join(dir, input), "utf8"));
  const entry = document.records.find(row => row.id === "microbial-fuel-cell");
  entry.citations = [];
  const used = new Set(document.records.flatMap(row => row.citations.map(claim => claim.source_id)));
  document.sources = document.sources.filter(source => used.has(source.id));
  fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
  const result = spawnSync(process.execPath, [script, "--root", dir], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const exported = JSON.parse(fs.readFileSync(path.join(dir, data, "taxonomy-audit.json"), "utf8"));
  const pending = exported.records.find(row => row.id === entry.id);
  assert.equal(pending.complete_entry_review, false);
  assert.deepEqual(pending.claim_citations, []);
  require("../04_interactive_presentation/taxonomy-claim-sources.js");
  const html = globalThis.AtlasTaxonomyCitations.render(pending.claim_citations);
  assert.match(html, /Full review of this entry remains pending/);
  assert.match(html, /No claim-level citation has been added/);
  assert.ok(!html.includes("<li>"));
  assert.ok(!html.includes("Source copy retrieved:"));
});
