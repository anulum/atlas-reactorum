// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — entry-owned classification and development evidence.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const api = require("../04_interactive_presentation/taxonomy-author-review.js");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const fixture = loadAuthorReviewFixture(path.resolve(__dirname, ".."));
test("the actual catalogue keeps overlapping facets and scoped historical stages without entry acceptance", () => {
  const before = JSON.stringify(fixture.review);
  const result = api.read(fixture.review, fixture.baseline);
  assert.equal(
    result.records.reduce((n, row) => n + row.facets.length, 0),
    138,
  );
  const attained = result.records.flatMap((row) =>
    row.development_assessments.map((item) => ({
      entry: row.entry_id,
      stage: item.stage,
      object: item.evidence_object,
      scope: item.scope,
    })),
  );
  assert.deepEqual(
    attained.map((item) => [item.entry, item.stage, item.object]),
    [
      ["pwr", "industrial", "operation"],
      ["integral-pwr", "industrial", "operation"],
      ["bwr", "industrial", "operation"],
      ["heavy-water-pressure-vessel-reactor", "industrial", "operation"],
      ["magnox-gas-cooled-reactor", "industrial", "operation"],
      ["prismatic-htgr", "industrial", "operation"],
      ["pebble-bed-htgr", "industrial", "operation"],
      ["sodium-fast-reactor", "industrial", "operation"],
      ["lead-bismuth-fast-reactor", "industrial", "operation"],
      ["thermal-liquid-fuel-molten-salt-reactor", "laboratory", "experiment"],
      ["continuous-stirred-tank-reactor-cstr", "laboratory", "operation"],
      ["cstr-cascade", "laboratory", "operation"],
      ["circulating-fluidised-bed-reactor", "industrial", "operation"],
      ["airlift-reactor", "pilot", "operation"],
      ["molten-carbonate-fuel-cell", "industrial", "operation"],
      ["solid-oxide-fuel-cell", "industrial", "operation"],
      ["dielectric-barrier-discharge-reactor", "industrial", "operation"],
      ["chemostat", "laboratory", "operation"],
      ["cell-retention-perfusion-bioreactor", "laboratory", "operation"],
      ["nuclear-heat-coupled-to-hydrogen-production", "pilot", "operation"],
      ["muon-catalysed-fusion", "laboratory", "experiment"],
    ],
  );
  const hydrogen = attained.find(
    (item) => item.entry === "nuclear-heat-coupled-to-hydrogen-production",
  );
  const muon = attained.find((item) => item.entry === "muon-catalysed-fusion");
  const marine = attained.find((item) => item.entry === "integral-pwr");
  const msre = attained.find(
    (item) => item.entry === "thermal-liquid-fuel-molten-salt-reactor",
  );
  assert.ok(hydrogen && muon && marine && msre);
  assert.match(hydrogen.scope, /electricity-powered/);
  assert.match(muon.scope, /reaction mechanism/);
  assert.match(marine.scope, /Manufacturer-attributed historical marine/);
  assert.match(msre.scope, /not a commercial or fast-spectrum/);
  assert.ok(
    result.records.every(
      (row) =>
        row.complete_entry_review === true && row.independent_review === null,
    ),
  );
  assert.equal(JSON.stringify(fixture.review), before);
});
for (const fault of [
  "empty-facets",
  "duplicate-facet",
  "missing-role",
  "unknown-axis",
  "facet-no-evidence",
  "facet-foreign-claim",
  "facet-foreign-observation",
  "stage-no-evidence",
  "stage-claim-only",
  "stage-foreign-claim",
  "stage-foreign-observation",
  "duplicate-stage",
  "stage-forecast",
  "stage-wrong-topic",
  "stage-wrong-object",
  "industrial-experiment",
  "unknown-stage",
  "unknown-object",
  "unknown-observed-object",
  "facet-extra",
  "stage-extra",
]) {
  test("the whole native reader refuses dimension fault " + fault, () => {
    const doc = structuredClone(fixture.review);
    const row = doc.records[0],
      facet = row.facets[0],
      stage = row.development_assessments[0];
    const hydrogen = doc.records.find(
      (item) => item.entry_id === "nuclear-heat-coupled-to-hydrogen-production",
    );
    const muon = doc.records.find(
      (item) => item.entry_id === "muon-catalysed-fusion",
    );
    assert.ok(hydrogen && muon);
    if (fault === "empty-facets") row.facets = [];
    else if (fault === "duplicate-facet")
      row.facets.push(structuredClone(facet));
    else if (fault === "missing-role") facet.value = "subtype";
    else if (fault === "unknown-axis") facet.axis = "unknown";
    else if (fault === "facet-no-evidence") facet.claim_ids = [];
    else if (fault === "facet-foreign-claim")
      facet.claim_ids = ["integral-pwr:classification:1"];
    else if (fault === "facet-foreign-observation")
      facet.observation_ids = [hydrogen.observations[0].id];
    else if (fault === "stage-no-evidence") stage.observation_ids = [];
    else if (fault === "stage-claim-only") {
      stage.observation_ids = [];
      stage.claim_ids = ["pwr:strength:1"];
    } else if (fault === "stage-foreign-claim")
      stage.claim_ids = ["integral-pwr:classification:1"];
    else if (fault === "stage-foreign-observation")
      stage.observation_ids = [hydrogen.observations[0].id];
    else if (fault === "duplicate-stage")
      row.development_assessments.push(structuredClone(stage));
    else if (fault === "stage-forecast")
      hydrogen.development_assessments[0].observation_ids = [
        hydrogen.observations[1].id,
      ];
    else if (fault === "stage-wrong-topic")
      row.observations[0].topic = "classification";
    else if (fault === "stage-wrong-object")
      stage.evidence_object = "experiment";
    else if (fault === "industrial-experiment")
      muon.development_assessments[0].stage = "industrial";
    else if (fault === "unknown-stage")
      Object.assign(stage, { stage: "unknown" });
    else if (fault === "unknown-object")
      Object.assign(stage, { evidence_object: "unknown" });
    else if (fault === "unknown-observed-object")
      Object.assign(row.observations[0], { evidence_object: "unknown" });
    else if (fault === "facet-extra") Object.assign(facet, { extra: true });
    else Object.assign(stage, { extra: true });
    assert.throws(() => api.read(doc, fixture.baseline));
  });
}
