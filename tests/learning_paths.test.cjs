// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original learning evidence, checks and versioned links
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createHash } = require("node:crypto");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
require("../04_interactive_presentation/taxonomy-comparison.js");
require("../04_interactive_presentation/learning-path-catalogue.js");
require("../04_interactive_presentation/learning-paths.js");
const api = globalThis.AtlasLearningPaths;
const root = path.resolve(__dirname, "..");
const document = JSON.parse(fs.readFileSync(path.join(root, "metadata/evidence_profiles/profiles.json"), "utf8"));
const window = {};
vm.runInNewContext(fs.readFileSync(path.join(root, "04_interactive_presentation/data/taxonomy-expanded.js"), "utf8"), { window });
const rows = JSON.parse(JSON.stringify(window.REACTOR_TAXONOMY));
const paths = api.listPaths();
const page = "https://example.org/atlas/index.html?language=en#taxonomy";

test("data and authored learning definitions have independently verifiable SHA-256 identities", async () => {
  const expected = value => createHash("sha256").update(JSON.stringify(value)).digest("hex");
  const snapshot = await api.snapshot(document);
  assert.deepEqual(snapshot, { profile_sha256: expected(document), learning_sha256: expected(globalThis.AtlasLearningCatalogue) });
  const editable = api.listPaths();
  editable[0].question = "An unrelated question";
  assert.deepEqual(api.listPaths(), paths);
  assert.equal(paths.length, 6);
  const edited = structuredClone(document);
  edited.records.at(-1).parameters[0].reason += " More context";
  assert.notEqual((await api.snapshot(edited)).profile_sha256, snapshot.profile_sha256);
  assert.equal((await api.snapshot(edited)).learning_sha256, snapshot.learning_sha256);
});

for (const learning of paths) {
  test(`${learning.id}: both depths retain every original claim, locator, rights and learning objective`, async () => {
    const snapshot = await api.snapshot(document);
    const original = await api.readPath(document, snapshot, learning.id);
    assert.equal(original.schema_version, "atlas-learning-session-1.0.0");
    assert.deepEqual(original.inputs, document.inputs);
    assert.deepEqual(original.path, learning);
    assert.deepEqual(original.profiles, learning.entry_ids.map(id => document.records.find(profile => profile.entry_id === id)));
    const used = new Set(original.profiles.flatMap(profile => profile.claims.map(claim => claim.citation.source_id)));
    assert.deepEqual(original.sources, document.sources.filter(source => used.has(source.id)));
    assert.equal(original.metadata_license, "AGPL-3.0-or-later");
    assert.equal(original.source_rights, "catalogue-only; original not redistributed");
    assert.ok(original.profiles.every(profile => !profile.review_disposition.complete_entry_review));
    for (const depth of ["overview", "research"]) {
      const rendered = await api.renderPath(document, snapshot, learning.id, depth, rows);
      assert.deepEqual(rendered.bundle, original);
      assert.ok(rendered.html.includes(learning.objective));
      assert.ok(rendered.html.includes(learning.question));
      assert.ok(rendered.html.includes("not-established"));
      for (const profile of original.profiles) {
        const row = rows.find(row => row.id === profile.entry_id);
        const full = globalThis.AtlasTaxonomyEvidenceProfiles.render(document, document.inputs.taxonomy_sha256, row);
        assert.ok(rendered.html.includes(full));
        assert.ok(rendered.html.includes(profile.taxonomy_record.evidence_scope));
      }
      assert.equal(rendered.html.includes("Inspect the original evidence profile and sources"), depth === "overview");
    }
    const correct = await api.assess(document, snapshot, learning.id, learning.answer_entry_id);
    assert.equal(correct.correct, true);
    assert.equal(correct.supporting_claim.original_statement, learning.answer_statement);
    assert.equal(correct.supporting_claim.citation.id, learning.answer_claim_id);
    assert.match(correct.message, /matches the cited statement/);
    assert.deepEqual(correct.snapshot, snapshot);
    for (const answer of [...learning.entry_ids.filter(id => id !== learning.answer_entry_id), "not-established"]) {
      const feedback = await api.assess(document, snapshot, learning.id, answer);
      assert.equal(feedback.correct, false);
      assert.deepEqual(feedback.supporting_claim, correct.supporting_claim);
      assert.match(feedback.message, /Re-read the cited statement/);
    }
    await assert.rejects(api.assess(document, snapshot, learning.id, "unknown"), /outside this path/);
  });
}

for (const expected of [null, {}, {profile_sha256: "bad", learning_sha256: "a".repeat(64)},
  {profile_sha256: "a".repeat(64), learning_sha256: "BAD"}]) {
  test(`malformed learning versions are refused: ${JSON.stringify(expected)}`, async () => {
    await assert.rejects(api.readPath(document, expected, paths[0].id), /hashes are invalid/);
    assert.throws(() => api.shareUrl(page, expected, paths[0].id, "overview"));
  });
}

for (const field of ["profile_sha256", "learning_sha256"]) {
  test(`stale ${field} never substitutes current source content`, async () => {
    const snapshot = await api.snapshot(document);
    snapshot[field] = "0".repeat(64);
    await assert.rejects(api.readPath(document, snapshot, paths[0].id), /not substituted/);
  });
}

test("missing, altered and misbound answer statements refuse the same publicly exported path", async () => {
  for (const mutate of [
    profile => { profile.claims = profile.claims.filter(claim => claim.claim_id !== paths[0].answer_claim_id); },
    profile => { profile.claims.find(claim => claim.claim_id === paths[0].answer_claim_id).original_statement += " Changed"; },
    profile => { profile.claims.find(claim => claim.claim_id === paths[0].answer_claim_id).citation.id = "unknown"; },
    profile => { profile.claims.find(claim => claim.claim_id === paths[0].answer_claim_id).citation.statement += " Changed"; },
  ]) {
    const edited = structuredClone(document);
    mutate(edited.records.find(profile => profile.entry_id === paths[0].answer_entry_id));
    await assert.rejects(api.readPath(edited, await api.snapshot(edited), paths[0].id), /original source statement/);
  }
});

test("unavailable profiles, sources and real taxonomy rows refuse instead of inventing examples", async () => {
  const snapshot = await api.snapshot(document);
  await assert.rejects(api.readPath(document, snapshot, "unknown"), /unavailable/);
  await assert.rejects(api.renderPath(document, snapshot, paths[0].id, "future", rows), /unavailable/);
  await assert.rejects(api.renderPath(document, snapshot, paths[0].id, "overview", []), /actual learning example/);
  const editedRows = structuredClone(rows);
  editedRows[0].principle += " Changed";
  await assert.rejects(api.renderPath(document, snapshot, paths[0].id, "overview", editedRows), /differs/);
  const missing = structuredClone(document);
  missing.records = missing.records.filter(profile => profile.entry_id !== "bwr");
  missing.record_count = missing.records.length;
  await assert.rejects(api.readPath(missing, await api.snapshot(missing), paths[0].id), /does not exist/);
  const source = structuredClone(document);
  source.sources = [];
  await assert.rejects(api.readPath(source, await api.snapshot(source), paths[0].id), /source is missing/);
  await assert.rejects(api.snapshot(null));
});

test("in-flight input edits cannot join an earlier snapshot to a later rendered taxonomy row", async () => {
  const editable = structuredClone(document);
  const actualRows = structuredClone(rows);
  const snapshot = await api.snapshot(editable);
  const rendering = api.renderPath(editable, snapshot, paths[0].id, "overview", actualRows);
  editable.records[0].taxonomy_record.principle += " Later";
  actualRows[0].principle += " Later";
  const result = await rendering;
  assert.deepEqual(result, await api.renderPath(document, snapshot, paths[0].id, "overview", rows));
});

test("original example names escape all HTML metacharacters in the visible controls", async () => {
  const edited = structuredClone(document);
  const actualRows = structuredClone(rows);
  const name = '<img src=x onerror="bad">&\'';
  edited.records[0].taxonomy_record.name = name;
  edited.records[0].bound_values.name = name;
  actualRows[0].name = name;
  const result = await api.renderPath(edited, await api.snapshot(edited), paths[0].id, "research", actualRows);
  assert.ok(result.html.includes("&lt;img src=x onerror=&quot;bad&quot;&gt;&amp;&#39;"));
  assert.equal(result.html.includes(name), false);
});

for (const url of [page, "http://localhost:8080/index.html", "file:///atlas/index.html"]) {
  test(`versioned learning link retains path, depth, both hashes and document location: ${url}`, async () => {
    const snapshot = await api.snapshot(document);
    for (const learning of paths) {
      for (const depth of ["overview", "research"]) {
        const shared = api.shareUrl(url, snapshot, learning.id, depth);
        assert.deepEqual(api.readUrl(shared), { snapshot, pathId: learning.id, depth });
        assert.equal(new URL(shared).pathname, new URL(url).pathname);
        assert.equal(new URL(shared).search, new URL(url).search);
        assert.equal(api.shareUrl(shared, snapshot, learning.id, depth), shared);
      }
    }
    assert.equal(api.readUrl(url), null);
  });
}

for (const url of ["data:text/html,example", "javascript:void(0)", "https://user@example.org/", "https://:password@example.org/", "invalid"]) {
  test(`learning links refuse unsupported or credential-bearing URLs: ${url}`, async () => {
    assert.throws(() => api.shareUrl(url, validVersion, paths[0].id, "overview"));
  });
}
const validVersion = { profile_sha256: "a".repeat(64), learning_sha256: "b".repeat(64) };

test("missing, duplicate, future, unknown and malformed linked fields are refused", async () => {
  const snapshot = await api.snapshot(document);
  const shared = api.shareUrl(page, snapshot, paths[0].id, "overview");
  for (const field of ["version", "profile", "lesson", "path", "view"]) {
    const missing = new URL(shared);
    const query = new URLSearchParams(missing.hash.slice(7));
    query.delete(field); missing.hash = "learn?" + query;
    assert.throws(() => api.readUrl(missing.href));
    const duplicate = new URL(shared);
    const doubled = new URLSearchParams(duplicate.hash.slice(7));
    doubled.append(field, doubled.get(field)); duplicate.hash = "learn?" + doubled;
    assert.throws(() => api.readUrl(duplicate.href));
  }
  for (const [field, value] of [["version", "2"], ["profile", "bad"], ["lesson", "bad"], ["path", "unknown"], ["view", "future"], ["extra", "true"]]) {
    const broken = new URL(shared);
    const query = new URLSearchParams(broken.hash.slice(7));
    query.set(field, value); broken.hash = "learn?" + query;
    assert.throws(() => api.readUrl(broken.href));
  }
  assert.equal(api.readUrl(page + "compare?version=1"), null);
});
