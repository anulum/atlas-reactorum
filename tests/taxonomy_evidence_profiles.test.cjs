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
const path = require("node:path");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
const api = globalThis.AtlasTaxonomyEvidenceProfiles;
const root = path.resolve(__dirname, "..");
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");
const { findRequired } = require("./taxonomy_citation_fixture.cjs");
const { document, rows } = loadProfileFixture(root);
const snapshot = document.inputs.taxonomy_sha256;

test("native profile loading uses the configured PATH interpreter when its explicit override is absent", () => {
  const selected = process.env.ATLAS_PYTHON;
  delete process.env.ATLAS_PYTHON;
  try {
    assert.deepEqual(loadProfileFixture(root), { document, rows });
  } finally {
    if (selected === undefined) delete process.env.ATLAS_PYTHON;
    else process.env.ATLAS_PYTHON = selected;
  }
});

/**
 * Select the actual missing-value parameter without treating it as a number.
 * @param {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceProfile} profile Original profile under test.
 * @returns {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasMissingParameter} Existing explicit missing-value record.
 */
function missingParameter(profile) {
  const parameter = profile.parameters[0];
  assert.notEqual(parameter.state, "known");
  assert.ok(parameter.state !== "known");
  return parameter;
}

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
    const exported =
      /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEntryEvidenceExport} */ (
        JSON.parse(api.exportProfile(document, snapshot, row.id))
      );
    assert.equal(exported.schema_version, "atlas-entry-evidence-1.0.0");
    assert.equal(exported.selected_entry_id, row.id);
    assert.deepEqual(exported.profile, profile);
    assert.equal(
      exported.profile.review_disposition.complete_entry_review,
      false,
    );
    assert.deepEqual(exported.inputs, document.inputs);
    const used = new Set(
      profile.claims.map((claim) => claim.citation.source_id),
    );
    assert.deepEqual(
      exported.sources,
      document.sources.filter((source) => used.has(source.id)),
    );
    const download = html.match(
      /href="data:application\/json;charset=utf-8,([^"]+)"/,
    );
    assert.ok(download);
    const encoded = download[1];
    assert.deepEqual(JSON.parse(decodeURIComponent(encoded)), exported);
    count += profile.claims.length;
  }
  assert.equal(count, 599);
});

/** @type {[string, (document: import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument) => import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument|null][]} */
const readerMutations = [
  ["null document", () => null],
  [
    "wrong version",
    (d) => {
      Reflect.set(d, "schema_version", "unsupported");
      return d;
    },
  ],
  [
    "wrong snapshot",
    (d) => {
      d.inputs.taxonomy_sha256 = "0".repeat(64);
      return d;
    },
  ],
  [
    "nonarray records",
    (d) => {
      Reflect.set(d, "records", {});
      return d;
    },
  ],
  [
    "incomplete count",
    (d) => {
      d.records.pop();
      return d;
    },
  ],
  [
    "duplicate last ID",
    (d) => {
      d.records[d.records.length - 1].entry_id = d.records[0].entry_id;
      return d;
    },
  ],
  [
    "whole approval",
    (d) => {
      Reflect.set(
        d.records[0].review_disposition,
        "complete_entry_review",
        true,
      );
      return d;
    },
  ],
  [
    "classification promotion",
    (d) => {
      Reflect.set(
        d.records[0].review_disposition.classification,
        "state",
        "accepted",
      );
      return d;
    },
  ],
  [
    "invented peer review",
    (d) => {
      Reflect.set(d.records[0].review_disposition, "independent_review", {});
      return d;
    },
  ],
  [
    "final entity decision",
    (d) => {
      Reflect.set(d.records[0].entity_kind, "decision", "accepted");
      return d;
    },
  ],
];
for (const [label, mutate] of readerMutations) {
  test(`explicit reader refuses ${label}`, () => {
    const damaged = mutate(structuredClone(document));
    assert.throws(() => api.readProfile(damaged, snapshot, rows[0].id));
  });
}

test("reader refuses an unknown ID and renderer refuses any bound-value drift", () => {
  assert.throws(
    () => api.readProfile(document, snapshot, "unknown"),
    /does not exist/,
  );
  const changed = structuredClone(rows[0]);
  changed.principle += " Invented";
  assert.throws(() => api.render(document, snapshot, changed), /differs/);
  const changedContext = structuredClone(rows[0]);
  changedContext.mode = "invented operating mode";
  assert.throws(
    () => api.render(document, snapshot, changedContext),
    /context differs/,
  );
});

/** @type {[string, (document: import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument) => void][]} */
const rendererMutations = [
  [
    "missing source",
    (d) => {
      const id = d.records[0].claims[0].citation.source_id;
      d.sources = d.sources.filter((s) => s.id !== id);
    },
  ],
  [
    "claim identity",
    (d) => {
      d.records[0].claims[0].claim_id = "invented";
    },
  ],
  [
    "source statement",
    (d) => {
      d.records[0].claims[0].original_statement = "invented";
    },
  ],
];
for (const [label, mutate] of rendererMutations) {
  test(`renderer refuses inconsistent ${label}`, () => {
    const d = structuredClone(document);
    mutate(d);
    assert.throws(() => api.render(d, snapshot, rows[0]));
    if (label === "missing source")
      assert.throws(
        () => api.exportProfile(d, snapshot, rows[0].id),
        /source is missing/,
      );
  });
}

test("zero remains a value while missing states retain their reason and exact original text", () => {
  const d = structuredClone(document);
  /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasKnownParameter} */
  const parameter = {
    id: "test",
    state: "known",
    value: 0,
    unit: "K",
    conditions: "explicit",
    system_boundary: "test boundary",
    claim_ids: [d.records[0].claims[0].claim_id],
    conversion_method: "identity",
    original_text: "A zero value for renderer verification",
  };
  d.records[0].parameters = [parameter];
  assert.match(api.render(d, snapshot, rows[0]), /test: 0 K/);
  for (const state of /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasMissingParameter["state"][]} */ ([
    "not_reported",
    "not_reviewed",
    "not_applicable",
    "disputed",
  ])) {
    d.records[0].parameters = [
      {
        id: "test",
        state,
        reason: "A documented reason",
        original_text: "Original text",
      },
    ];
    assert.match(api.render(d, snapshot, rows[0]), /A documented reason/);
  }
  for (const value of [NaN, Infinity, -Infinity]) {
    d.records[0].parameters = [{ ...parameter, value }];
    assert.throws(() => api.render(d, snapshot, rows[0]), /not finite/);
  }
  for (const bad of [
    { id: "test", state: "missing", reason: "reason" },
    { id: "test", state: "not_reviewed", reason: null },
    { id: "test", state: "not_reviewed", reason: " " },
  ]) {
    Reflect.set(d.records[0], "parameters", [bad]);
    assert.throws(() => api.render(d, snapshot, rows[0]), /state and reason/);
  }
});

test("authored explanation and historic questions cannot inject markup or executable links", () => {
  const d = structuredClone(document);
  const hostile = "&<script>window.injected=true</script>\"'";
  d.records[0].review_disposition.classification.questions[0] = hostile;
  missingParameter(d.records[0]).reason = hostile;
  const html = api.render(d, snapshot, rows[0]);
  assert.ok(!html.includes("<script>"));
  assert.match(html, /&amp;&lt;script&gt;/);
  assert.match(html, /&quot;&#39;/);
  const retained = JSON.parse(api.exportProfile(d, snapshot, rows[0].id));
  assert.equal(
    retained.profile.review_disposition.classification.questions[0],
    hostile,
  );
});

test("retained-source unknown retrieval dates and exact printed/PDF/section scopes survive export", () => {
  const row = findRequired(rows, (row) =>
    findRequired(document.records, (p) => p.entry_id === row.id).claims.some(
      (claim) =>
        findRequired(
          document.sources,
          (source) => source.id === claim.citation.source_id,
        ).captured_at === null,
    ),
  );
  const exported =
    /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEntryEvidenceExport} */ (
      JSON.parse(api.exportProfile(document, snapshot, row.id))
    );
  assert.ok(exported.sources.some((source) => source.captured_at === null));
  assert.match(
    api.render(document, snapshot, row),
    /original retrieval date unknown/,
  );
  for (const claim of exported.profile.claims)
    assert.deepEqual(
      claim.citation,
      findRequired(
        findRequired(document.records, (p) => p.entry_id === row.id).claims,
        (c) => c.claim_id === claim.claim_id,
      ).citation,
    );
});
