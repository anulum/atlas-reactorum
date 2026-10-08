// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original catalogue history, identity, chronology and source integrity
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { createHash } = require("node:crypto");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
require("../04_interactive_presentation/taxonomy-comparison.js");
require("../04_interactive_presentation/evidence-history.js");
const api = globalThis.AtlasEvidenceHistory;
const {
  loadHistoryProfiles,
  missingParameter,
} = require("./evidence_history_fixture.cjs");
const { findRequired } = require("./taxonomy_citation_fixture.cjs");
const document = loadHistoryProfiles(path.resolve(__dirname, ".."));
const times = [
  "2026-10-03T07:20:00.000Z",
  "2026-10-04T07:20:00.000Z",
  "2026-10-05T07:20:00.000Z",
  "2026-10-06T07:20:00.000Z",
];
/**
 * Hash original JSON member order independently of the browser implementation.
 * @param {unknown} value Original journal, profile or revision.
 * @returns {string} Native SHA-256 of the original complete serialised content.
 */
const originalHash = (value) =>
  createHash("sha256").update(JSON.stringify(value)).digest("hex");

test("initial real whole import preserves all135 identities,599 original claims and all source metadata", async () => {
  const before = JSON.stringify(document);
  const history = await api.importProfiles(null, document, times[0]);
  assert.equal(history.snapshots.length, 1);
  assert.equal(history.imports.length, 1);
  assert.deepEqual(history.snapshots[0].document, document);
  assert.equal(history.snapshots[0].profile_sha256, originalHash(document));
  assert.equal(history.snapshots[0].document.records.length, 135);
  assert.equal(
    history.snapshots[0].document.records.flatMap((profile) => profile.claims)
      .length,
    599,
  );
  await api.validate(history);
  const digest = await api.digest(history);
  assert.equal(digest, originalHash(history));
  for (const profile of document.records) {
    const claim = profile.claims[profile.claims.length - 1];
    const selected = await api.readClaim(
      history,
      digest,
      profile.entry_id,
      claim.claim_id,
    );
    assert.equal(selected.revisions.length, 1);
    assert.deepEqual(selected.revisions[0].claim, claim);
    const source = findRequired(
      document.sources,
      (source) => source.id === claim.citation.source_id,
    );
    assert.deepEqual(selected.revisions[0].source, source);
    assert.equal(
      selected.revisions[0].dates.source_acquired_at,
      source.captured_at,
    );
    assert.equal(
      selected.revisions[0].dates.claim_reviewed_on,
      claim.citation.reviewed_on,
    );
    assert.equal(selected.revisions[0].dates.source_event_on, null);
    assert.equal(selected.revisions[0].dates.source_published_on, null);
    assert.equal(selected.revisions[0].dates.atlas_observed_at, times[0]);
    assert.equal(
      selected.source_rights,
      "catalogue-only; original not redistributed",
    );
    const { revision_sha256, ...revision } = selected.revisions[0];
    assert.equal(revision_sha256, originalHash(revision));
  }
  assert.equal(JSON.stringify(document), before);
});

test("repeat import is byte-identical and unrelated profile edits do not invent a selected-claim revision", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  const repeat = await api.importProfiles(history, document, times[1]);
  assert.deepEqual(repeat, history);
  const changed = structuredClone(document);
  missingParameter(changed.records[changed.records.length - 1]).reason +=
    " Clarification in a controlled input.";
  const updated = await api.importProfiles(history, changed, times[1]);
  assert.equal(updated.imports.length, 2);
  assert.deepEqual(updated.snapshots[0], history.snapshots[0]);
  const record = await api.readClaim(
    updated,
    await api.digest(updated),
    "pwr",
    "pwr:classification:1",
  );
  assert.equal(record.revisions.length, 1);
  assert.deepEqual(history, repeat);
});

test("changed wording and source locator create visible preserved revisions without rewriting prior snapshot", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  const changed = structuredClone(document);
  const claim = changed.records[0].claims[0];
  claim.original_statement += " Controlled source correction test.";
  claim.citation.statement = claim.original_statement;
  claim.citation.section += " / corrected locator";
  findRequired(
    changed.sources,
    (source) => source.id === claim.citation.source_id,
  ).sha256 = "a".repeat(64);
  const next = await api.importProfiles(history, changed, times[1]);
  assert.deepEqual(next.snapshots[0], history.snapshots[0]);
  const record = await api.readClaim(
    next,
    await api.digest(next),
    "pwr",
    claim.claim_id,
  );
  assert.equal(record.revisions.length, 2);
  assert.deepEqual(record.revisions[0].claim, document.records[0].claims[0]);
  assert.deepEqual(record.revisions[1].claim, claim);
  assert.deepEqual(record.revisions[1].changes, [
    "claim-or-locator",
    "source-metadata",
  ]);
  assert.notEqual(
    record.revisions[0].revision_sha256,
    record.revisions[1].revision_sha256,
  );
  await assert.rejects(
    api.readClaim(next, await api.digest(history), "pwr", claim.claim_id),
    /not substituted/,
  );
  await assert.rejects(
    api.readClaim(next, "bad", "pwr", claim.claim_id),
    /not substituted/,
  );
});

test("source-only changes are revisions even when original wording is identical", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  const changed = structuredClone(document);
  const id = changed.records[0].claims[0].citation.source_id;
  const retained = findRequired(changed.sources, (source) => source.id === id);
  retained.capture_method = "retained-source-review";
  retained.captured_at = null;
  const next = await api.importProfiles(history, changed, times[1]);
  const record = await api.readClaim(
    next,
    await api.digest(next),
    "pwr",
    "pwr:classification:1",
  );
  assert.deepEqual(record.revisions[1].changes, ["source-metadata"]);
  assert.deepEqual(record.revisions[1].claim, record.revisions[0].claim);
  assert.equal(record.revisions[1].dates.source_acquired_at, null);
});

test("a removed profile remains identifiable in history and its return has a distinct dated revision", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  const absent = structuredClone(document);
  absent.records.shift();
  absent.record_count--;
  const removed = await api.importProfiles(history, absent, times[1]);
  const returned = await api.importProfiles(removed, document, times[2]);
  assert.equal(returned.snapshots.length, 2);
  assert.equal(returned.imports.length, 3);
  const record = await api.readClaim(
    returned,
    await api.digest(returned),
    "pwr",
    "pwr:classification:1",
  );
  assert.deepEqual(
    record.revisions.map((revision) => revision.state),
    ["present", "not-in-snapshot", "present"],
  );
  assert.equal(record.revisions[1].claim, null);
  assert.equal(record.revisions[1].source, null);
  assert.equal(record.revisions[1].dates.claim_reviewed_on, null);
  assert.deepEqual(record.revisions[0].claim, record.revisions[2].claim);
  assert.notEqual(
    record.revisions[0].revision_sha256,
    record.revisions[2].revision_sha256,
  );
  const firstAbsent = await api.importProfiles(null, absent, times[0]);
  const laterPresent = await api.importProfiles(
    firstAbsent,
    document,
    times[1],
  );
  const later = await api.readClaim(
    laterPresent,
    await api.digest(laterPresent),
    "pwr",
    "pwr:classification:1",
  );
  assert.equal(later.revisions[0].state, "not-in-snapshot");
  await assert.rejects(
    api.readClaim(history, await api.digest(history), "unknown", "unknown"),
    /unavailable/,
  );
  await assert.rejects(
    api.readClaim(history, await api.digest(history), "pwr", "unknown"),
    /unavailable/,
  );
});

test("removing only a claim retains other claims and never resolves absence by substituting current wording", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  const changed = structuredClone(document);
  changed.records[0].claims.shift();
  const next = await api.importProfiles(history, changed, times[1]);
  const record = await api.readClaim(
    next,
    await api.digest(next),
    "pwr",
    "pwr:classification:1",
  );
  assert.equal(record.revisions[1].state, "not-in-snapshot");
  assert.equal(record.revisions[1].claim, null);
});

test("in-flight edits do not alter either imported snapshots or exported revisions", async () => {
  const editable = structuredClone(document);
  const importing = api.importProfiles(null, editable, times[0]);
  editable.records[0].claims[0].original_statement = "Later unrelated wording";
  const history = await importing;
  assert.deepEqual(history.snapshots[0].document, document);
  const digest = await api.digest(history);
  const reading = api.readClaim(history, digest, "pwr", "pwr:classification:1");
  history.snapshots[0].document.records[0].claims[0].original_statement =
    "Later mutation";
  assert.deepEqual(
    (await reading).revisions[0].claim,
    document.records[0].claims[0],
  );
});

for (const time of [
  null,
  "2026-10-03",
  "2026-02-30T07:20:00.000Z",
  "2026-10-03T07:20:00Z",
  "not-a-date",
]) {
  test(`invalid observation is refused before any snapshot is accepted: ${time}`, async () => {
    assert.throws(() => api.observation(time), /timestamp/);
    await assert.rejects(api.importProfiles(null, document, time), /timestamp/);
  });
}

test("broken source and duplicate claim identities refuse the real import", async () => {
  /** @type {((content: import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument) => void)[]} */
  const changes = [
    (content) => {
      Reflect.set(content, "sources", null);
    },
    (content) => {
      content.sources.push(content.sources[0]);
    },
    (content) => {
      content.records[0].claims.push(content.records[0].claims[0]);
    },
  ];
  for (const alter of changes) {
    const changed = structuredClone(document);
    alter(changed);
    await assert.rejects(
      api.importProfiles(null, changed, times[0]),
      /duplicated|unavailable/,
    );
  }
  await assert.rejects(api.importProfiles(null, null, times[0]), /unavailable/);
});

test("altered snapshots, unsupported formats and orphan/reversed observations refuse retained history", async () => {
  const history = await api.importProfiles(null, document, times[0]);
  /** @type {((value: import("../04_interactive_presentation/evidence-history.js").AtlasEvidenceJournal) => void)[]} */
  const changes = [
    (value) => {
      value.schema_version = "future";
    },
    (value) => {
      value.metadata_license = "unknown";
    },
    (value) => {
      value.source_rights = "unrestricted";
    },
    (value) => {
      Reflect.set(value, "snapshots", null);
    },
    (value) => {
      value.snapshots = [];
    },
    (value) => {
      Reflect.set(value, "imports", null);
    },
    (value) => {
      value.imports = [];
    },
    (value) => {
      value.snapshots[0].profile_sha256 = "bad";
    },
    (value) => {
      value.snapshots[0].document.record_count--;
    },
    (value) => {
      value.snapshots.push(value.snapshots[0]);
    },
    (value) => {
      value.imports[0].profile_sha256 = "0".repeat(64);
    },
    (value) => {
      value.imports.push({ ...value.imports[0], observed_at: times[1] });
    },
    (value) => {
      value.imports.push({ ...value.imports[0], observed_at: times[0] });
    },
  ];
  const malformed = [
    null,
    {},
    ...changes.map((alter) => {
      const value = structuredClone(history);
      alter(value);
      return value;
    }),
  ];
  for (const value of malformed)
    await assert.rejects(() => Reflect.apply(api.validate, api, [value]));
  const changed = structuredClone(document);
  missingParameter(changed.records[0]).reason += " Changed";
  const orphan = structuredClone(history);
  orphan.snapshots.push({
    profile_sha256: originalHash(changed),
    document: changed,
  });
  await assert.rejects(api.validate(orphan), /unobserved/);
  await assert.rejects(
    api.importProfiles(history, changed, times[0]),
    /predecessor/,
  );
  await assert.rejects(
    api.importProfiles(history, changed, "2026-10-02T07:20:00.000Z"),
    /predecessor/,
  );
});
