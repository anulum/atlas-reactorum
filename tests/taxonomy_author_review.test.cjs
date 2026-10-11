// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual whole author assessment and source-bound refusal behavior.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const api = require("../04_interactive_presentation/taxonomy-author-review.js");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const fixture = loadAuthorReviewFixture(path.resolve(__dirname, ".."));
test("the actual all135 source assessment preserves every value, claim, source and temporal role", () => {
  const before = JSON.stringify(fixture);
  const result = api.read(fixture.review, fixture.baseline);
  assert.equal(result, fixture.review);
  assert.equal(result.records.length, 135);
  assert.equal(
    result.records.reduce((n, row) => n + Object.keys(row.fields).length, 0),
    2835,
  );
  assert.equal(result.additional_sources.length, 11);
  assert.equal(
    result.records.reduce((n, row) => n + row.observations.length, 0),
    31,
  );
  assert.equal(JSON.stringify(fixture), before);
});
test("completed field review preserves unknown outcomes and refuses independent acceptance", () => {
  const doc = api.read(fixture.review, fixture.baseline);
  assert.equal(doc.schema_version, "atlas-author-review-1.1.0");
  for (const [index, row] of doc.records.entries()) {
    assert.equal(row.complete_entry_review, true);
    assert.equal(row.review_scope, "all-original-fields-and-selected-sources");
    assert.equal(row.review_basis, "author-source-inspection");
    assert.equal(row.independent_review, null);
    assert.equal(row.current_activity, "unknown");
    assert.equal(row.fields.control.disposition, "unscored");
    assert.equal(row.fields.scale.disposition, "unscored");
    assert.equal(
      fixture.baseline.records[index].review_disposition.complete_entry_review,
      false,
    );
  }
  assert.equal(
    doc.records.filter(
      (row) => row.fields.maturity.disposition === "unsupported",
    ).length,
    8,
  );
  for (const change of [
    { current_activity: "operating" },
    { review_scope: "all-hardware-qualified" },
    { review_basis: "independent-review" },
    { independent_review: { accepted: true } },
    { complete_entry_review: false },
  ]) {
    const damaged = structuredClone(fixture.review);
    Object.assign(damaged.records[damaged.records.length - 1], change);
    assert.throws(() => api.read(damaged, fixture.baseline));
  }
});
for (const fault of [
  "order",
  "original-value",
  "unknown-claim",
  "unknown-source",
  "missing-source",
  "editorial-science",
  "false-score",
  "incomplete-entry",
  "review-scope",
  "review-basis",
  "independent-acceptance",
  "future-event",
  "pages",
  "unused-source",
]) {
  test("actual whole input refuses " + fault, () => {
    const doc = structuredClone(fixture.review);
    const row = doc.records[0];
    if (fault === "order") doc.records.reverse();
    else if (fault === "original-value")
      row.fields.principle.original_value = "changed source statement";
    else if (fault === "unknown-claim")
      row.fields.principle.claim_ids = ["absent:principle:1"];
    else if (fault === "unknown-source")
      row.fields.principle.source_ids = ["absent-source"];
    else if (fault === "missing-source") row.fields.principle.source_ids = [];
    else if (fault === "editorial-science")
      row.fields.principle.disposition = "editorial";
    else if (fault === "false-score")
      row.fields.principle.disposition = "unscored";
    else if (fault === "incomplete-entry")
      Object.assign(row, { complete_entry_review: false });
    else if (fault === "review-scope")
      Object.assign(row, { review_scope: "independently-qualified-hardware" });
    else if (fault === "review-basis")
      Object.assign(row, { review_basis: "independent-review" });
    else if (fault === "independent-acceptance")
      Object.assign(row, { independent_review: { accepted: true } });
    else if (fault === "future-event")
      row.observations[0].event_date = {
        value: "2030-01-01",
        precision: "day",
      };
    else if (fault === "pages") row.observations[0].pdf_pages = [100000];
    else
      for (const entry of doc.records)
        entry.observations = entry.observations.filter(
          (item) => item.source_id !== doc.additional_sources[0].id,
        );
    assert.throws(
      () => api.read(doc, fixture.baseline),
      /Author|author|source|score|scientific|future|attained/,
    );
  });
}

for (const fault of [
  "version",
  "author",
  "hash",
  "category",
  "extra-field",
  "field-note",
  "field-state",
  "unbound-science",
  "source-url",
  "source-hash",
  "source-format",
  "source-count",
  "source-method",
  "source-capture",
  "retained-capture",
  "later-capture",
  "duplicate-source",
  "duplicate-observation",
  "observation-source",
  "observation-topic",
  "observation-role",
  "duplicate-page",
  "negative-page",
  "printed-page",
  "html-page",
  "month",
  "year",
  "day",
  "unknown-precision",
  "precision",
  "after-publication",
  "future-publication",
  "after-capture",
  "array-value-order",
  "array-value-length",
  "reference-duplicate",
  "reference-nontext",
  "record-id",
]) {
  test("whole native author input refuses " + fault, () => {
    const doc = structuredClone(fixture.review);
    const row = doc.records[0];
    const source = doc.additional_sources[0];
    const observation = row.observations[0];
    const html = doc.records
      .flatMap((entry) => entry.observations)
      .find((item) => item.source_id === source.id);
    assert.ok(html);
    if (fault === "version") Object.assign(doc, { schema_version: "unknown" });
    else if (fault === "author") Object.assign(doc, { author: "unknown" });
    else if (fault === "hash")
      doc.baseline_inputs.audit_sha256 = "0".repeat(64);
    else if (fault === "category") row.entity_category = "unknown";
    else if (fault === "extra-field")
      Object.assign(row.fields.principle, { extra: true });
    else if (fault === "field-note") row.fields.principle.assessment = "";
    else if (fault === "field-state")
      Object.assign(row.fields.principle, { disposition: "unknown" });
    else if (fault === "unbound-science") {
      row.fields.principle.source_ids = [];
      row.fields.principle.claim_ids = [];
    } else if (fault === "source-url") source.url = "http://publisher.example/";
    else if (fault === "source-hash") source.sha256 = "bad";
    else if (fault === "source-format")
      Object.assign(source, { format: "png" });
    else if (fault === "source-count") source.page_count = 1;
    else if (fault === "source-method")
      Object.assign(source, { capture_method: "unknown" });
    else if (fault === "source-capture")
      source.captured_at = "2026-10-08T07:28:31+01:00";
    else if (fault === "retained-capture")
      source.capture_method = "retained-source-review";
    else if (fault === "later-capture")
      source.captured_at = "2030-01-01T00:00:00Z";
    else if (fault === "duplicate-source")
      source.id = fixture.baseline.sources[0].id;
    else if (fault === "duplicate-observation") html.id = observation.id;
    else if (fault === "observation-source")
      observation.source_id = "absent-source";
    else if (fault === "observation-topic") observation.topic = "unknown";
    else if (fault === "observation-role")
      Object.assign(observation, { temporal_role: "unknown" });
    else if (fault === "duplicate-page") observation.pdf_pages = [1, 1];
    else if (fault === "negative-page") observation.pdf_pages = [-1];
    else if (fault === "printed-page") observation.printed_pages = [];
    else if (fault === "html-page") {
      html.pdf_pages = [1];
      html.printed_pages = ["1"];
    } else if (fault === "month")
      observation.event_date = { value: "2024-13", precision: "month" };
    else if (fault === "year")
      observation.event_date = { value: "0000", precision: "year" };
    else if (fault === "day")
      observation.event_date = { value: "2024-02-30", precision: "day" };
    else if (fault === "unknown-precision")
      observation.event_date = { value: null, precision: "day" };
    else if (fault === "precision")
      Object.assign(observation.event_date, { precision: "unknown" });
    else if (fault === "after-publication")
      observation.published_date = { value: "2023", precision: "year" };
    else if (fault === "future-publication")
      observation.published_date = { value: "2030", precision: "year" };
    else if (fault === "after-capture")
      source.captured_at = "2024-02-01T00:00:00Z";
    else if (fault === "array-value-order")
      row.fields.source_ids.original_value = ["other-source"];
    else if (fault === "array-value-length")
      row.fields.source_ids.original_value = [];
    else if (fault === "reference-duplicate")
      row.fields.principle.claim_ids.push(row.fields.principle.claim_ids[0]);
    else if (fault === "reference-nontext")
      Object.assign(row.fields.principle, { claim_ids: [17] });
    else row.entry_id = "Upper";
    assert.throws(() => api.read(doc, fixture.baseline));
  });
}

test("inherited wire members and nonobject collections refuse through the real reader", () => {
  for (const input of [null, [], 17, "author review"])
    assert.throws(() => api.read(input, fixture.baseline));
  const doc = structuredClone(fixture.review);
  assert.throws(() => api.read(Object.create(doc), fixture.baseline));
  Object.assign(doc, { records: 17 });
  assert.throws(() => api.read(doc, fixture.baseline));
});

test("incomplete original baseline and future source inspection refuse before admission", () => {
  for (const fault of [
    "version",
    "empty",
    "count",
    "missing-review",
    "future-inspection",
  ]) {
    const baseline = structuredClone(fixture.baseline);
    const review = structuredClone(fixture.review);
    if (fault === "version")
      Object.assign(baseline, { schema_version: "unknown" });
    else if (fault === "empty") baseline.records = [];
    else if (fault === "count") baseline.record_count--;
    else if (fault === "missing-review") review.records.pop();
    else baseline.records[0].claims[0].citation.reviewed_on = "2030-01-01";
    assert.throws(
      () => api.read(review, baseline),
      /complete catalogue|source inspection/,
    );
  }
});

test("the original classic-script files admit the same entire input in their native VM boundary", () => {
  const vm = require("node:vm");
  const fs = require("node:fs");
  const context = vm.createContext({
    structuredClone,
    review: fixture.review,
    baseline: fixture.baseline,
  });
  for (const name of [
    "author-review-values.js",
    "author-review-dimensions.js",
    "author-review-revisions.js",
    "taxonomy-author-review.js",
  ]) {
    const source = path.resolve(
      __dirname,
      "../04_interactive_presentation",
      name,
    );
    vm.runInContext(fs.readFileSync(source, "utf8"), context, {
      filename: source,
    });
  }
  /** @type {unknown} Original classic-script result before complete equality assertion. */
  const result = vm.runInContext(
    "AtlasTaxonomyAuthorReview.read(review,baseline)",
    context,
  );
  assert.equal(result, fixture.review);
});
