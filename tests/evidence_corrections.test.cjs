// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — pending correction provenance and explicit non-publishing curator decisions
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { createHash } = require("node:crypto");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
require("../04_interactive_presentation/taxonomy-comparison.js");
require("../04_interactive_presentation/evidence-history.js");
require("../04_interactive_presentation/evidence-corrections.js");
const historyApi = globalThis.AtlasEvidenceHistory;
const api = globalThis.AtlasEvidenceCorrections;
const { loadHistoryProfiles } = require("./evidence_history_fixture.cjs");
const { findRequired } = require("./taxonomy_citation_fixture.cjs");
const document = loadHistoryProfiles(path.resolve(__dirname, ".."));
const time = "2026-10-03T07:20:00.000Z";
const input = {
  proposed_statement: "A controlled proposed classification correction.",
  source_url: findRequired(
    document.sources,
    (source) => source.id === document.records[0].claims[0].citation.source_id,
  ).url,
  locator: "2.1.3 Classification, printed page4",
  reason: "Explain the scope of the original classification.",
  submitted_by: "Named test contributor",
  proposed_at: time,
};
/** @type {import("../04_interactive_presentation/evidence-corrections.js").AtlasCuratorReview} */
const evidence = {
  decision: "accepted-for-editing",
  reviewed_by: "Named test curator",
  reviewed_at: "2026-10-04T07:20:00.000Z",
  reason: "The cited locator supports the proposed narrower wording.",
  source_url: input.source_url,
  locator: input.locator,
};
/**
 * Bind the original selected classification claim to a real whole-journal import.
 * @returns {Promise<{history: import("../04_interactive_presentation/evidence-history.js").AtlasEvidenceJournal, digest: string, revision: Extract<import("../04_interactive_presentation/evidence-history.js").AtlasClaimRevision, {state: "present"}>}>} Source-bound original present revision and whole-journal identity.
 */
async function context() {
  const history = await historyApi.importProfiles(null, document, time);
  const digest = await historyApi.digest(history);
  const record = await historyApi.readClaim(
    history,
    digest,
    "pwr",
    "pwr:classification:1",
  );
  const revision = record.revisions[0];
  assert.equal(revision.state, "present");
  assert.ok(revision.state === "present");
  return { history, digest, revision };
}

test("pending proposal retains an exact original revision and never changes accepted source data", async () => {
  const { history, digest, revision } = await context();
  const before = JSON.stringify(history);
  const proposal = await api.propose(
    history,
    digest,
    "pwr",
    "pwr:classification:1",
    revision.revision_sha256,
    input,
  );
  assert.equal(proposal.state, "pending");
  assert.equal(proposal.review, null);
  assert.equal(proposal.history_sha256, digest);
  assert.deepEqual(proposal.original_revision, revision);
  assert.deepEqual(proposal.proposal, input);
  assert.equal(
    proposal.source_rights,
    "catalogue-only; original not redistributed",
  );
  assert.equal(
    proposal.publication_effect,
    "none; accepted source data remain unchanged",
  );
  const { proposal_sha256, ...body } = proposal;
  assert.equal(
    proposal_sha256,
    createHash("sha256").update(JSON.stringify(body)).digest("hex"),
  );
  assert.equal(JSON.stringify(history), before);
  assert.deepEqual(history.snapshots[0].document, document);
});

for (const decision of ["accepted-for-editing", "rejected"]) {
  test(`explicit ${decision} preserves the pending artefact, source data and reviewer evidence`, async () => {
    const { history, digest, revision } = await context();
    const proposal = await api.propose(
      history,
      digest,
      "pwr",
      "pwr:classification:1",
      revision.revision_sha256,
      input,
    );
    const before = JSON.stringify(proposal);
    const reviewed = await api.reviewProposal(proposal, {
      ...evidence,
      decision,
    });
    assert.equal(reviewed.state, decision);
    assert.equal(reviewed.pending_proposal_sha256, proposal.proposal_sha256);
    assert.deepEqual(reviewed.review, { ...evidence, decision });
    assert.deepEqual(reviewed.original_revision, revision);
    assert.deepEqual(reviewed.proposal, input);
    assert.equal(reviewed.publication_effect, proposal.publication_effect);
    assert.equal(JSON.stringify(proposal), before);
    assert.deepEqual(history.snapshots[0].document, document);
    assert.equal(
      reviewed.review_sha256,
      await historyApi.digest({
        pending_proposal_sha256: proposal.proposal_sha256,
        review: reviewed.review,
      }),
    );
    await assert.rejects(api.reviewProposal(reviewed, evidence), /pending/);
  });
}

test("unknown, removed, stale and unchanged source revisions cannot produce a misleading proposal", async () => {
  const { history, digest, revision } = await context();
  await assert.rejects(
    api.propose(
      history,
      digest,
      "pwr",
      "pwr:classification:1",
      "0".repeat(64),
      input,
    ),
    /unavailable/,
  );
  await assert.rejects(
    api.propose(
      history,
      "0".repeat(64),
      "pwr",
      "pwr:classification:1",
      revision.revision_sha256,
      input,
    ),
    /not substituted/,
  );
  await assert.rejects(
    api.propose(
      history,
      digest,
      "pwr",
      "pwr:classification:1",
      revision.revision_sha256,
      { ...input, proposed_statement: revision.claim.original_statement },
    ),
    /different/,
  );
  const removed = structuredClone(document);
  removed.records.shift();
  removed.record_count--;
  const updated = await historyApi.importProfiles(
    history,
    removed,
    "2026-10-04T07:20:00.000Z",
  );
  const updatedDigest = await historyApi.digest(updated);
  const absent = (
    await historyApi.readClaim(
      updated,
      updatedDigest,
      "pwr",
      "pwr:classification:1",
    )
  ).revisions[1];
  await assert.rejects(
    api.propose(
      updated,
      updatedDigest,
      "pwr",
      "pwr:classification:1",
      absent.revision_sha256,
      input,
    ),
    /unavailable/,
  );
});

test("pending inputs require all named source-bound fields and refuse unknown keys and malformed URLs", async () => {
  const { history, digest, revision } = await context();
  for (const key of Object.keys(input)) {
    for (const invalid of ["", "   ", null, 12]) {
      await assert.rejects(
        api.propose(
          history,
          digest,
          "pwr",
          "pwr:classification:1",
          revision.revision_sha256,
          { ...input, [key]: invalid },
        ),
      );
    }
  }
  for (const altered of [
    null,
    { ...input, extra: "unknown" },
    ...[
      "http://example.org/",
      "https://user@example.org/",
      "https://:secret@example.org/",
      "javascript:void(0)",
      "not-a-url",
    ].map((source_url) => ({ ...input, source_url })),
    { ...input, proposed_at: "2026-02-30T07:20:00.000Z" },
  ]) {
    await assert.rejects(
      api.propose(
        history,
        digest,
        "pwr",
        "pwr:classification:1",
        revision.revision_sha256,
        altered,
      ),
    );
  }
});

test("tampering and unsupported pending formats cannot be relabelled as reviewed", async () => {
  const { history, digest, revision } = await context();
  const proposal = await api.propose(
    history,
    digest,
    "pwr",
    "pwr:classification:1",
    revision.revision_sha256,
    input,
  );
  /** @type {((value: import("../04_interactive_presentation/evidence-corrections.js").AtlasCorrectionProposal) => void)[]} */
  const changes = [
    (value) => {
      value.schema_version = "future";
    },
    (value) => {
      value.state = "accepted";
    },
    (value) => {
      value.review = evidence;
    },
    (value) => {
      value.proposal.reason += " Altered";
    },
    (value) => {
      value.proposal_sha256 = "bad";
    },
  ];
  for (const change of changes) {
    const altered = structuredClone(proposal);
    change(altered);
    await assert.rejects(api.reviewProposal(altered, evidence), /pending/);
  }
  const badInput = structuredClone(proposal);
  badInput.proposal.source_url = "http://example.org/";
  const body = Object.fromEntries(
    Object.entries(badInput).filter(([key]) => key !== "proposal_sha256"),
  );
  badInput.proposal_sha256 = await historyApi.digest(body);
  await assert.rejects(api.reviewProposal(badInput, evidence), /HTTPS/);
});

test("review requires a dated explicit decision and locator; it cannot precede the proposal", async () => {
  const { history, digest, revision } = await context();
  const proposal = await api.propose(
    history,
    digest,
    "pwr",
    "pwr:classification:1",
    revision.revision_sha256,
    input,
  );
  for (const key of Object.keys(evidence)) {
    for (const invalid of ["", "   ", null, 12]) {
      await assert.rejects(
        api.reviewProposal(proposal, { ...evidence, [key]: invalid }),
      );
    }
  }
  for (const altered of [
    null,
    { ...evidence, extra: "unknown" },
    { ...evidence, decision: "published" },
    ...[
      "http://example.org/",
      "https://user@example.org/",
      "https://:secret@example.org/",
      "not-a-url",
    ].map((source_url) => ({ ...evidence, source_url })),
    { ...evidence, reviewed_at: "2026-02-30T07:20:00.000Z" },
    { ...evidence, reviewed_at: "2026-10-02T07:20:00.000Z" },
  ]) {
    await assert.rejects(api.reviewProposal(proposal, altered));
  }
});

test("in-flight contributor and curator input edits do not join different proposal versions", async () => {
  const { history, digest, revision } = await context();
  const editable = structuredClone(input);
  const creating = api.propose(
    history,
    digest,
    "pwr",
    "pwr:classification:1",
    revision.revision_sha256,
    editable,
  );
  editable.proposed_statement = "Later text";
  const proposal = await creating;
  assert.deepEqual(proposal.proposal, input);
  const curator = structuredClone(evidence);
  const reviewing = api.reviewProposal(proposal, curator);
  curator.reason = "Later different rationale";
  proposal.proposal.reason = "Later mutation";
  const reviewed = await reviewing;
  assert.deepEqual(reviewed.review, evidence);
  assert.deepEqual(reviewed.proposal, input);
});
