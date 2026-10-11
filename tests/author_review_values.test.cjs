// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual source metadata and date-bound admission surface.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const values = require("../04_interactive_presentation/author-review-values.js");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const fixture = loadAuthorReviewFixture(path.resolve(__dirname, ".."));
test("all original and actual supplemental source metadata retain exact custody", () => {
  for (const source of [
    ...fixture.baseline.sources,
    ...fixture.review.additional_sources,
  ])
    assert.equal(values.source(source), source);
});
test("source-declared day, month and forecast-year ranges retain their precision", () => {
  const pwr = fixture.review.records.find((row) => row.entry_id === "pwr");
  const hydrogen = fixture.review.records.find(
    (row) => row.entry_id === "nuclear-heat-coupled-to-hydrogen-production",
  );
  assert.ok(pwr && hydrogen);
  assert.deepEqual(values.dateBounds(pwr.observations[0].event_date), [
    "2024-12-31",
    "2024-12-31",
  ]);
  assert.deepEqual(values.dateBounds(hydrogen.observations[0].event_date), [
    "2023-03-01",
    "2023-03-31",
  ]);
  assert.deepEqual(values.dateBounds(hydrogen.observations[1].event_date), [
    "2029-01-01",
    "2029-12-31",
  ]);
  assert.equal(values.dateBounds(pwr.observations[0].published_date), null);
  assert.equal(hydrogen.observations[1].temporal_role, "forecast");
});
