// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — full-catalogue evidence profile browser API conformance
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
const api = globalThis.AtlasTaxonomyEvidenceProfiles;
const root = path.resolve(__dirname, "..");
const document = JSON.parse(fs.readFileSync(path.join(root, "metadata/evidence_profiles/profiles.json"), "utf8"));
const snapshot = document.inputs.taxonomy_sha256;
const window = {};
vm.runInNewContext(fs.readFileSync(path.join(root, "04_interactive_presentation/data/taxonomy-expanded.js"), "utf8"), { window });
const rows = JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY));

test("every one of 135 actual entries renders and downloads all original citations and sources", () => {
  let count = 0;
  for (const row of rows) {
    const profile = api.readProfile(document, snapshot, row.id);
    const html = api.render(document, snapshot, row);
    assert.match(html, /Classification<\/dt><dd>Open/);
    assert.match(html, /Source rights/);
    assert.match(html, /Historical classification questions/);
    assert.match(html, /not a fresh finding/);
    assert.match(html, /temperature: not reviewed/);
    const exported = JSON.parse(api.exportProfile(document, snapshot, row.id));
    assert.equal(exported.schema_version, "atlas-entry-evidence-1.0.0");
    assert.equal(exported.selected_entry_id, row.id);
    assert.deepEqual(exported.profile, profile);
    assert.equal(exported.profile.review_disposition.complete_entry_review, false);
    assert.deepEqual(exported.inputs, document.inputs);
    const used = new Set(profile.claims.map(claim => claim.citation.source_id));
    assert.deepEqual(exported.sources, document.sources.filter(source => used.has(source.id)));
    const encoded = html.match(/href="data:application\/json;charset=utf-8,([^"]+)"/)[1];
    assert.deepEqual(JSON.parse(decodeURIComponent(encoded)), exported);
    count += profile.claims.length;
  }
  assert.equal(count, 599);
});

for (const [label, mutate] of [
  ["null document", () => null],
  ["wrong version", d => { d.schema_version = "unsupported"; return d; }],
  ["wrong snapshot", d => { d.inputs.taxonomy_sha256 = "0".repeat(64); return d; }],
  ["nonarray records", d => { d.records = {}; return d; }],
  ["incomplete count", d => { d.records.pop(); return d; }],
  ["duplicate last ID", d => { d.records.at(-1).entry_id = d.records[0].entry_id; return d; }],
  ["whole approval", d => { d.records[0].review_disposition.complete_entry_review = true; return d; }],
  ["classification promotion", d => { d.records[0].review_disposition.classification.state = "accepted"; return d; }],
  ["invented peer review", d => { d.records[0].review_disposition.independent_review = {}; return d; }],
  ["final entity decision", d => { d.records[0].entity_kind.decision = "accepted"; return d; }],
]) {
  test(`explicit reader refuses ${label}`, () => {
    const damaged = mutate(structuredClone(document));
    assert.throws(() => api.readProfile(damaged, snapshot, rows[0].id));
  });
}

test("reader refuses an unknown ID and renderer refuses any bound-value drift", () => {
  assert.throws(() => api.readProfile(document, snapshot, "unknown"), /does not exist/);
  const changed = structuredClone(rows[0]);
  changed.principle += " Invented";
  assert.throws(() => api.render(document, snapshot, changed), /differs/);
  const changedContext = structuredClone(rows[0]);
  changedContext.mode = "invented operating mode";
  assert.throws(() => api.render(document, snapshot, changedContext), /context differs/);
});

for (const [label, mutate] of [
  ["missing source", d => { const id = d.records[0].claims[0].citation.source_id; d.sources = d.sources.filter(s => s.id !== id); }],
  ["claim identity", d => { d.records[0].claims[0].claim_id = "invented"; }],
  ["source statement", d => { d.records[0].claims[0].original_statement = "invented"; }],
]) {
  test(`renderer refuses inconsistent ${label}`, () => {
    const d = structuredClone(document);
    mutate(d);
    assert.throws(() => api.render(d, snapshot, rows[0]));
    if (label === "missing source") assert.throws(() => api.exportProfile(d, snapshot, rows[0].id), /source is missing/);
  });
}

test("zero remains a value while missing states retain their reason and exact original text", () => {
  const d = structuredClone(document);
  const parameter = {id: "test", state: "known", value: 0, unit: "K", conditions: "explicit",
    system_boundary: "test boundary", claim_ids: [d.records[0].claims[0].claim_id],
    conversion_method: "identity", original_text: "A zero value for renderer verification"};
  d.records[0].parameters = [parameter];
  assert.match(api.render(d, snapshot, rows[0]), /test: 0 K/);
  for (const state of ["not_reported", "not_reviewed", "not_applicable", "disputed"]) {
    d.records[0].parameters = [{id: "test", state, reason: "A documented reason", original_text: "Original text"}];
    assert.match(api.render(d, snapshot, rows[0]), /A documented reason/);
  }
  for (const value of [NaN, Infinity, -Infinity]) {
    d.records[0].parameters = [{...parameter, value}];
    assert.throws(() => api.render(d, snapshot, rows[0]), /not finite/);
  }
  for (const bad of [
    {id: "test", state: "missing", reason: "reason"},
    {id: "test", state: "not_reviewed", reason: null},
    {id: "test", state: "not_reviewed", reason: " "},
  ]) {
    d.records[0].parameters = [bad];
    assert.throws(() => api.render(d, snapshot, rows[0]), /state and reason/);
  }
});

test("authored explanation and historic questions cannot inject markup or executable links", () => {
  const d = structuredClone(document);
  const hostile = "&<script>window.injected=true</script>\"'";
  d.records[0].review_disposition.classification.questions[0] = hostile;
  d.records[0].parameters[0].reason = hostile;
  const html = api.render(d, snapshot, rows[0]);
  assert.ok(!html.includes("<script>"));
  assert.match(html, /&amp;&lt;script&gt;/);
  assert.match(html, /&quot;&#39;/);
  const retained = JSON.parse(api.exportProfile(d, snapshot, rows[0].id));
  assert.equal(retained.profile.review_disposition.classification.questions[0], hostile);
});

test("retained-source unknown retrieval dates and exact printed/PDF/section scopes survive export", () => {
  const row = rows.find(row => document.records.find(p => p.entry_id === row.id).claims.some(
    claim => document.sources.find(source => source.id === claim.citation.source_id).captured_at === null));
  const exported = JSON.parse(api.exportProfile(document, snapshot, row.id));
  assert.ok(exported.sources.some(source => source.captured_at === null));
  assert.match(api.render(document, snapshot, row), /original retrieval date unknown/);
  for (const claim of exported.profile.claims) assert.deepEqual(claim.citation,
    document.records.find(p => p.entry_id === row.id).claims.find(c => c.claim_id === claim.claim_id).citation);
});
