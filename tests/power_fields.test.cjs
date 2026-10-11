// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native and classic power documentary conformance
"use strict";

const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path"),
  { execFileSync } = require("node:child_process"),
  vm = require("node:vm");
const {
  actualPage,
  originalDocument,
  loadScripts,
} = require("./catalogue_dom_fixture.cjs");
const C = require("../04_interactive_presentation/power-source-contract.js"),
  P = require("../04_interactive_presentation/power-field-contract.js"),
  R = require("../04_interactive_presentation/power-field-assertions.js");
require("../04_interactive_presentation/application-data.js");
const E = require("../04_interactive_presentation/facility-export.js");
const root = path.resolve(__dirname, "..");
const packet = C.mapping(
  JSON.parse(
    execFileSync(
      process.env.ATLAS_PYTHON || path.join(root, ".venv/bin/python"),
      [
        "-c",
        "import json; from tests.test_power_contract import original_packet; print(json.dumps(original_packet(),ensure_ascii=False))",
      ],
      { cwd: root, encoding: "utf8" },
    ),
  ),
);
const mutations = C.sequence(
  C.mapping(
    JSON.parse(
      fs.readFileSync(path.join(root, "tests/power_mutations.json"), "utf8"),
    ),
  ).cases,
);
for (const input of mutations) {
  const caseRow = C.mapping(input);
  test("same original-source admission as Python: " + caseRow.name, () => {
    const damaged = structuredClone(packet),
      keys = C.sequence(caseRow.path);
    let target = damaged[String(caseRow.root)];
    for (const key of keys.slice(0, -1))
      target = Array.isArray(target)
        ? target[Number(key)]
        : C.mapping(target)[String(key)];
    const key = keys.at(-1);
    if (Array.isArray(target)) target[Number(key)] = caseRow.value;
    else if (caseRow.op === "delete") delete C.mapping(target)[String(key)];
    else C.mapping(target)[String(key)] = caseRow.value;
    if (caseRow.accepted)
      P.project(damaged.baseline, damaged.ledger, damaged.sources);
    else
      assert.throws(() =>
        P.project(damaged.baseline, damaged.ledger, damaged.sources),
      );
  });
}
test("document dates keep real calendar precision separate from capture", () => {
  for (const [precision, value] of [
    ["unknown", ""],
    ["year", "2020"],
    ["month", "2020-02"],
    ["day", "2020-02-29"],
    ["month_range", "2020-01/2020-12"],
  ])
    C.documentDate({
      date_precision: precision,
      document_date: value,
      date_basis: "report_period",
    });
  for (const [precision, value] of [
    ["unknown", "2020"],
    ["year", "0000"],
    ["month", "2020-13"],
    ["day", "2021-02-29"],
    ["month_range", "2020"],
    ["month_range", "2020-13/2021-01"],
    ["month_range", "2021-01/2020-12"],
  ])
    assert.throws(() =>
      C.documentDate({
        date_precision: precision,
        document_date: value,
        date_basis: "report_period",
      }),
    );
  for (const value of [null, [], false]) assert.throws(() => C.mapping(value));
  for (const value of [null, "scalar"]) assert.throws(() => C.sequence(value));
  for (const value of [false, "BAD"]) assert.throws(() => C.digest(value));
  assert.equal(
    C.httpsUrl("https://example.org/document"),
    "https://example.org/document",
  );
  assert.throws(() => C.httpsUrl("broken"));
});
test("complete targets and documentary provenance refuse duplicate or invented support", () => {
  const baseline = C.sequence(packet.baseline),
    ledger = C.sequence(packet.ledger),
    sources = C.sequence(packet.sources);
  for (const [rows, fields] of [
    [[], ledger],
    [baseline.concat(baseline), ledger],
    [baseline, []],
    [baseline, ledger.concat(ledger)],
  ])
    assert.throws(() => P.project(rows, fields, sources));
  assert.throws(() => C.admitSources(sources.concat(sources)));
  const admitted = C.admitSources(sources),
    decision = C.mapping(ledger[0]),
    citation = C.mapping(C.sequence(decision.citations)[0]);
  for (const source of admitted.values())
    if (
      source.body_state === "context_only" ||
      source.body_state === "capture_attempt"
    ) {
      assert.throws(() =>
        C.admitCitations(
          [{ ...citation, source_id: source.source_id }],
          admitted,
          true,
        ),
      );
    }
  assert.throws(() => C.admitCitations([citation, citation], admitted, true));
  assert.throws(() => C.admitCitations([], admitted, true));
  assert.deepEqual(C.admitCitations([], admitted, false), []);
  const attempt = [...admitted.values()].find(
    (row) => row.body_state === "capture_attempt",
  );
  assert.ok(attempt);
  const observation = {
    basis: "Refusal",
    scope: "No factual support admitted",
    candidate_value: "",
    citations: [],
    capture_attempts: [attempt.source_id],
  };
  const held = {
    ...decision,
    disposition: "held",
    value: "",
    role: "",
    citations: [],
    observations: [observation],
  };
  P.project(baseline, [held, ...ledger.slice(1)], sources);
  for (const changes of [
    { value: "invented" },
    { role: "actual_operator" },
    { citations: [citation] },
    {
      observations: [
        {
          ...observation,
          capture_attempts: [attempt.source_id, attempt.source_id],
        },
      ],
    },
    {
      observations: [
        { ...observation, capture_attempts: [citation.source_id] },
      ],
    },
    { observations: [{ ...observation, capture_attempts: [] }] },
  ])
    assert.throws(() =>
      P.project(
        baseline,
        [{ ...held, ...changes }, ...ledger.slice(1)],
        sources,
      ),
    );
  const original = C.mapping(baseline[0]);
  assert.throws(() =>
    P.project([{ ...original, operator: "known" }], ledger, sources),
  );
});
test("actual complete dataset preserves roles, unresolved fields and all download decisions", () => {
  const rows = globalThis.AtlasApplicationData.facilities(
    originalDocument("global_reactors.sample"),
  );
  let decisions = 0;
  for (const row of rows) {
    const admitted = row.power_field_decisions;
    if (!admitted) {
      assert.equal(R.render(row), "");
      continue;
    }
    decisions += admitted.length;
    const html = R.render(row);
    assert.ok(html.includes("Power unit source review"));
    for (const decision of admitted) {
      assert.equal(decision.independent_review, null);
      if (decision.disposition === "qualified")
        assert.notEqual(R.label(row, decision.field, "Original"), "Original");
      else assert.equal(R.label(row, decision.field, "Original"), "Original");
    }
    assert.equal(R.label(row, "unknown-field", "Original"), "Original");
  }
  assert.equal(decisions, 930);
  assert.deepEqual(JSON.parse(E.serialize(rows, "json")), rows);
  const csv = E.serialize(rows, "csv");
  assert.ok(csv.includes("power_field_decisions"));
  const row = rows.find((row) =>
    row.power_field_decisions?.some((d) => d.disposition === "qualified"),
  );
  assert.ok(row?.power_field_decisions);
  for (const changes of [
    { operator: "invented" },
    { country: "different", source_country: undefined },
    { lat: 0 },
    { source_status: "generating" },
    { power_field_decisions: [] },
  ])
    assert.throws(() =>
      globalThis.AtlasApplicationData.facilities([{ ...row, ...changes }]),
    );
  const first = structuredClone(row.power_field_decisions);
  first[0].original_context.lat = "invalid";
  assert.throws(() => P.admitPresentation(first, row));
  const mixed = structuredClone(row.power_field_decisions);
  const selected = mixed.find(
    (decision) => decision.disposition === "qualified",
  );
  assert.ok(selected);
  const citation = selected.citations[0];
  assert.ok(citation);
  selected.observations.push({
    basis: "Contradictory custody",
    scope: "Must refuse",
    candidate_value: "",
    citations: [{ ...citation, body_bytes: 1 }],
    capture_attempts: [],
  });
  assert.throws(() => P.admitPresentation(mixed, row));
});
test("actual classic consumer and native consumer project identical original cells", (context) => {
  const dom = actualPage(context);
  loadScripts(dom, [
    "presentation-text.js",
    "power-source-contract.js",
    "power-field-contract.js",
    "power-field-assertions.js",
    "application-data.js",
    "data/global_reactors.sample.js",
    "facility-export.js",
  ]);
  dom.window.document.body.dataset.packet = JSON.stringify(packet);
  const encoded = vm.runInContext(
    "JSON.stringify(PowerFieldContract.project(...['baseline','ledger','sources'].map(key=>JSON.parse(document.body.dataset.packet)[key])))",
    dom.getInternalVMContext(),
  );
  assert.deepEqual(
    JSON.parse(encoded),
    P.project(packet.baseline, packet.ledger, packet.sources),
  );
  const output = vm.runInContext(
    "JSON.stringify(AtlasApplicationData.facilities(REACTOR_FACILITIES).filter(row=>row.power_field_decisions).map(row=>PowerFieldAssertions.render(row)))",
    dom.getInternalVMContext(),
  );
  const rows = globalThis.AtlasApplicationData.facilities(
    originalDocument("global_reactors.sample"),
  );
  assert.deepEqual(
    JSON.parse(output),
    rows.filter((row) => row.power_field_decisions).map((row) => R.render(row)),
  );
});

test("an unavailable HTTP result stays a capture attempt in actual details", () => {
  const rows = globalThis.AtlasApplicationData.facilities(
    originalDocument("global_reactors.sample"),
  );
  const original = rows.find((row) =>
    row.power_field_decisions?.some((decision) =>
      decision.observations.some(
        (observation) => observation.capture_attempts.length,
      ),
    ),
  );
  assert.ok(original?.power_field_decisions);
  const row = structuredClone(original);
  assert.ok(row.power_field_decisions);
  for (const decision of row.power_field_decisions)
    for (const observation of decision.observations) {
      for (const attempt of observation.capture_attempts) {
        attempt.http_status = null;
        attempt.body_bytes = null;
        attempt.body_sha256 = "";
        attempt.body_complete = false;
      }
    }
  const admitted = globalThis.AtlasApplicationData.facilities([row])[0];
  assert.equal(admitted.operator, original.operator);
  assert.equal(admitted.reactor_type, original.reactor_type);
  assert.ok(R.render(admitted).includes("Capture attempt · HTTP unavailable"));
});
