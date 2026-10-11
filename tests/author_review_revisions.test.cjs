// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — explicit corrections and independent full taxonomy projection.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const api = require("../04_interactive_presentation/taxonomy-author-review.js");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const fixture = loadAuthorReviewFixture(path.resolve(__dirname, ".."));
test("all135 projected rows apply only the seven explicit source-supported field revisions and keep original contexts", () => {
  const before = JSON.stringify(fixture);
  const projected = api.project(fixture.review, fixture.baseline);
  assert.equal(projected.length, 135);
  const changed = [];
  for (const [index, row] of projected.entries()) {
    const original = fixture.baseline.records[index].taxonomy_record;
    assert.deepEqual(Object.keys(row), Object.keys(original));
    assert.equal(row.id, original.id);
    for (const key of Object.keys(original))
      if (
        JSON.stringify(row[/** @type {keyof typeof row} */ (key)]) !==
        JSON.stringify(original[/** @type {keyof typeof original} */ (key)])
      )
        changed.push([row.id, key, row[/** @type {keyof typeof row} */ (key)]]);
  }
  assert.deepEqual(changed, [
    ["integral-pwr", "maturity", "deployed"],
    ["phwr-candu", "name", "Pressure-tube PHWR including CANDU"],
    ["heavy-water-pressure-vessel-reactor", "maturity", "deployed"],
    ["magnox-gas-cooled-reactor", "maturity", "deployed"],
    ["prismatic-htgr", "maturity", "deployed"],
    ["lead-bismuth-fast-reactor", "maturity", "deployed"],
    [
      "nuclear-heat-coupled-to-hydrogen-production",
      "name",
      "Nuclear energy coupled to hydrogen production",
    ],
  ]);
  projected[0].source_ids.push("caller-mutation");
  projected[0].source_urls.reverse();
  assert.equal(JSON.stringify(fixture), before);
  assert.deepEqual(
    api.project(fixture.review, fixture.baseline)[0],
    fixture.baseline.records[0].taxonomy_record,
  );
});
for (const fault of [
  "duplicate",
  "unchanged",
  "missing",
  "unassessed",
  "identity",
  "empty",
  "unknown-field",
  "extra",
  "nonarray",
  "contextual-science",
  "last-entry",
]) {
  test("complete revision/projection admission refuses " + fault, () => {
    const doc = structuredClone(fixture.review);
    const row = doc.records.find((item) => item.entry_id === "phwr-candu");
    assert.ok(row);
    if (fault === "duplicate")
      row.revisions.push(structuredClone(row.revisions[0]));
    else if (fault === "unchanged")
      row.revisions[0].value = /** @type {string} */ (
        row.fields.name.original_value
      );
    else if (fault === "missing") row.revisions = [];
    else if (fault === "unassessed")
      doc.records[0].revisions = [
        { field: "name", value: "Unassessed PWR caption" },
      ];
    else if (fault === "identity")
      Object.assign(row.revisions[0], { field: "id" });
    else if (fault === "empty") row.revisions[0].value = "";
    else if (fault === "unknown-field")
      Object.assign(row.revisions[0], { field: "unknown" });
    else if (fault === "extra")
      Object.assign(row.revisions[0], { extra: true });
    else if (fault === "nonarray") Object.assign(row, { revisions: null });
    else if (fault === "contextual-science")
      row.fields.principle.disposition = "context-only";
    else {
      const last = doc.records.at(-1);
      assert.ok(last);
      last.fields.principle.original_value = "changed last original";
    }
    assert.throws(() => api.read(doc, fixture.baseline));
    assert.throws(() => api.project(doc, fixture.baseline));
  });
}
