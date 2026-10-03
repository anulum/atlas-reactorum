// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual original history presentation and versioned links
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
require("../04_interactive_presentation/taxonomy-comparison.js");
require("../04_interactive_presentation/evidence-history.js");
require("../04_interactive_presentation/evidence-history-render.js");
const historyApi = globalThis.AtlasEvidenceHistory;
const api = globalThis.AtlasEvidenceHistoryRender;
const document = JSON.parse(fs.readFileSync(path.join(__dirname, "../04_interactive_presentation/data/taxonomy-evidence-profiles.json"), "utf8"));
const dates = ["2026-10-03T07:20:00.000Z", "2026-10-04T07:20:00.000Z", "2026-10-05T07:20:00.000Z"];

test("real baseline presentation retains original claim/source and separates all date meanings", async () => {
  const history = await historyApi.importProfiles(null, document, dates[0]);
  const hash = await historyApi.digest(history);
  const result = await api.render(history, hash, "pwr", "pwr:classification:1");
  assert.deepEqual(result.bundle.revisions[0].claim, document.records[0].claims[0]);
  assert.equal(result.selected, result.bundle.revisions[0]);
  assert.ok(result.html.includes(document.records[0].claims[0].original_statement));
  assert.ok(result.html.includes("first recorded observation"));
  assert.ok(result.html.includes("Unknown / not recorded"));
  assert.ok(result.html.includes("source acquired at"));
  assert.ok(result.html.includes("claim reviewed on"));
  assert.ok(result.html.includes("source published on"));
  assert.ok(result.html.includes("first-journal-observation"));
  const explicit = await api.render(history, hash, "pwr", "pwr:classification:1", result.selected.revision_sha256);
  assert.deepEqual(explicit, result);
  await assert.rejects(api.render(history, hash, "pwr", "pwr:classification:1", "0".repeat(64)), /unavailable/);
  await assert.rejects(api.render(history, "0".repeat(64), "pwr", "pwr:classification:1"), /not substituted/);
});

test("changed original wording is escaped and old wording/source survive selected later observations", async () => {
  const original = await historyApi.importProfiles(null, document, dates[0]);
  const changed = structuredClone(document);
  const claim = changed.records[0].claims[0];
  claim.original_statement = "<img src=x onerror='bad'> & \"corrected\"";
  claim.citation.statement = claim.original_statement;
  claim.citation.section = "<script>locator</script>";
  claim.citation.scope = "Only <this> & 'that'";
  const source = changed.sources.find(source => source.id === claim.citation.source_id);
  source.title = "<iframe>source</iframe>";
  source.capture_method = "retained-source-review";
  source.captured_at = null;
  const next = await historyApi.importProfiles(original, changed, dates[1]);
  const hash = await historyApi.digest(next);
  const result = await api.render(next, hash, "pwr", claim.claim_id);
  assert.equal(result.bundle.revisions.length, 2);
  assert.deepEqual(result.bundle.revisions[0].claim, document.records[0].claims[0]);
  assert.deepEqual(result.bundle.revisions[1].claim, claim);
  assert.ok(result.html.includes("&lt;img src=x onerror=&#39;bad&#39;&gt; &amp; &quot;corrected&quot;"));
  assert.ok(result.html.includes("&lt;script&gt;locator&lt;/script&gt;"));
  assert.ok(result.html.includes("&lt;iframe&gt;source&lt;/iframe&gt;"));
  assert.equal(result.html.includes("<img"), false);
  assert.equal(result.html.includes("<script>"), false);
  assert.ok(result.html.includes("claim-or-locator, source-metadata"));
  const first = await api.render(next, hash, "pwr", claim.claim_id, result.bundle.revisions[0].revision_sha256);
  assert.deepEqual(first.selected.claim, document.records[0].claims[0]);
});

test("retired and returned claims render distinct retained observations without current substitution", async () => {
  const baseline = await historyApi.importProfiles(null, document, dates[0]);
  const absent = structuredClone(document);
  absent.records[0].claims.shift();
  const removed = await historyApi.importProfiles(baseline, absent, dates[1]);
  const returned = await historyApi.importProfiles(removed, document, dates[2]);
  const hash = await historyApi.digest(returned);
  const result = await api.render(returned, hash, "pwr", "pwr:classification:1");
  const disappearance = await api.render(returned, hash, "pwr", "pwr:classification:1", result.bundle.revisions[1].revision_sha256);
  assert.equal(disappearance.selected.state, "not-in-snapshot");
  assert.equal(disappearance.selected.claim, null);
  assert.ok(disappearance.html.includes("not present in this imported snapshot"));
  assert.equal(disappearance.bundle.revisions.length, 3);
  assert.notEqual(result.bundle.revisions[0].revision_sha256, result.bundle.revisions[2].revision_sha256);
});

test("exact historical links round-trip all identities on supported pages and retain query", () => {
  for (const page of ["https://example.test/index.html?lang=en#taxonomy", "http://localhost:8000/", "file:///tmp/atlas/index.html"]) {
    const url = api.shareUrl(page, "a".repeat(64), "pwr", "pwr:classification:1", "b".repeat(64));
    assert.deepEqual(api.readUrl(url), { historyHash: "a".repeat(64), entryId: "pwr", claimId: "pwr:classification:1", revisionHash: "b".repeat(64) });
    assert.equal(new URL(url).search, new URL(page).search);
  }
  assert.equal(api.readUrl("https://example.test/#taxonomy"), null);
  assert.equal(api.readUrl("https://example.test/#learn?version=1"), null);
  for (const page of ["ftp://example.test/", "https://user@example.test/", "https://user:pass@example.test/"]) {
    assert.throws(() => api.shareUrl(page, "a".repeat(64), "pwr", "pwr:classification:1", "b".repeat(64)), /unsupported/);
  }
});

test("missing/ambiguous historical fields and invalid identities refuse instead of resolving latest", () => {
  const valid = api.shareUrl("https://example.test/", "a".repeat(64), "pwr", "pwr:classification:1", "b".repeat(64));
  for (const field of ["version", "history", "entry", "claim", "revision"]) {
    for (const mutation of [query => query.delete(field), query => query.append(field, query.get(field))]) {
      const url = new URL(valid); const query = new URLSearchParams(url.hash.slice(9)); mutation(query);
      url.hash = "history?" + query.toString();
      assert.throws(() => api.readUrl(url.href), /invalid/);
    }
  }
  for (const [field, value] of [["version", "future"], ["unknown", "1"], ["history", "latest"], ["revision", "latest"], ["entry", ""], ["claim", ""]]) {
    const url = new URL(valid); const query = new URLSearchParams(url.hash.slice(9)); query.set(field, value);
    url.hash = "history?" + query.toString();
    assert.throws(() => api.readUrl(url.href));
  }
  for (const args of [["bad", "pwr", "claim", "b".repeat(64)], ["a".repeat(64), "pwr", "claim", "bad"],
    ["a".repeat(64), null, "claim", "b".repeat(64)], ["a".repeat(64), "", "claim", "b".repeat(64)],
    ["a".repeat(64), "pwr", null, "b".repeat(64)], ["a".repeat(64), "pwr", "", "b".repeat(64)]]) {
    assert.throws(() => api.shareUrl("https://example.test/", ...args), /unavailable/);
  }
});
