// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual authored construction, original defaults and source-key refusal.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const api = require("../04_interactive_presentation/taxonomy-construction.js");
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");
const root = path.resolve(__dirname, "..");
const fixture = loadProfileFixture(root);
const pwr = fixture.rows.find((row) => row.id === "pwr");
const bwr = fixture.rows.find((row) => row.id === "bwr");
assert.ok(pwr && bwr);

/**
 * Retain the actual original row's tuple cells before selecting optional authored overrides.
 * @param {import("../04_interactive_presentation/scripts/taxonomy_export_inputs.cjs").TaxonomyRow} row Complete source-validated original row.
 * @returns {import("../04_interactive_presentation/taxonomy-construction.js").TaxonomyDefinition} Original descriptive cells and explicit original kind.
 */
function definition(row) {
  return [
    row.name,
    null,
    row.maturity,
    row.evidence,
    row.principle,
    row.strength,
    row.challenge,
    row.kind,
  ];
}

test("real classic browser and native readers construct every original row and locator", () => {
  const dom = new JSDOM(
    fs.readFileSync(
      path.join(root, "04_interactive_presentation/index.html"),
      "utf8",
    ),
    { runScripts: "outside-only" },
  );
  try {
    dom.window.eval(
      fs.readFileSync(
        path.join(root, "04_interactive_presentation/taxonomy-construction.js"),
        "utf8",
      ),
    );
    dom.window.eval(
      fs.readFileSync(
        path.join(
          root,
          "04_interactive_presentation/data/taxonomy-expanded.js",
        ),
        "utf8",
      ),
    );
    assert.equal(
      JSON.stringify(dom.window.REACTOR_TAXONOMY),
      JSON.stringify(fixture.rows),
    );
    assert.equal(Object.keys(dom.window.REACTOR_TAXONOMY_SOURCES).length, 194);
    assert.equal(fixture.rows.length, 135);
  } finally {
    dom.window.close();
  }
});

test("source tables and selected inherited, missing or nontextual locators refuse", () => {
  for (const input of [null, undefined, false, 17, "source", []])
    assert.throws(() => api.create(input), /source table is unavailable/);
  for (const input of [
    {},
    Object.create({ nrc: pwr.source_urls[0] }),
    { nrc: 17 },
  ]) {
    const builder = api.create(input);
    assert.throws(
      () => builder.add(pwr.domain, pwr.family, "nrc", [definition(pwr)]),
      /source identity is unavailable/,
    );
    assert.deepEqual(builder.complete(), []);
  }
});

test("original default kind, source list, scope and review date remain explicit source defaults", () => {
  const builder = api.create({ nrc: pwr.source_urls[0] });
  const tuple = definition(pwr);
  tuple.length = 7;
  builder.add(pwr.domain, pwr.family, "nrc", [tuple]);
  const rows = builder.complete();
  assert.equal(rows[0].kind, "architecture");
  assert.equal(rows[0].reviewed_on, "2026-09-26");
  assert.equal(
    rows[0].evidence_scope,
    "Established process or reactor architecture; individual designs require separate qualification.",
  );
  assert.equal(rows[0].parent, pwr.family);
  assert.equal(rows[0].parent_id, null);
  assert.equal(rows[0].scale, null);
  assert.equal(rows[0].control, null);
  assert.deepEqual(rows[0].source_urls, [pwr.source_urls[0]]);
});

test("original entry-specific locators, scope and review dates override only their own family row", () => {
  const sources = { nrc: pwr.source_urls[0], bwr: bwr.source_urls[0] };
  const builder = api.create(sources);
  const first = definition(pwr);
  first[8] = {
    source: "nrc",
    evidence_scope: pwr.evidence_scope,
    reviewed_on: pwr.reviewed_on,
  };
  const second = definition(bwr);
  second[8] = {
    source: "bwr",
    evidence_scope: bwr.evidence_scope,
    reviewed_on: bwr.reviewed_on,
  };
  builder.add(pwr.domain, pwr.family, "nrc", [first, second]);
  const rows = builder.complete();
  assert.deepEqual(
    rows.map((row) => row.source_urls),
    [[sources.nrc], [sources.bwr]],
  );
  assert.deepEqual(
    rows.map((row) => row.reviewed_on),
    [pwr.reviewed_on, bwr.reviewed_on],
  );
  assert.deepEqual(
    rows.map((row) => row.evidence_scope),
    [pwr.evidence_scope, bwr.evidence_scope],
  );
  assert.equal(builder.complete(), rows);
});

test("source-based fusion and contested wording retains its original scope and absence of scores", () => {
  for (const identity of [
    "tokamak",
    "palladium-deuterium-electrochemical-lenr",
  ]) {
    const row = fixture.rows.find((candidate) => candidate.id === identity);
    assert.ok(row);
    const builder = api.create({ original: row.source_urls[0] });
    builder.add(row.domain, row.family, "original", [definition(row)]);
    const [result] = builder.complete();
    assert.equal(result.mode, row.mode);
    assert.match(
      result.evidence_scope,
      row.evidence === "contested"
        ? /Claim under dispute/
        : /experiments, components or analysis/,
    );
    assert.equal(result.scale, null);
    assert.equal(result.control, null);
  }
});

test("parent resolution runs after all entries and retains original stable identities", () => {
  const child = fixture.rows.find((row) => row.parent_id !== null);
  assert.ok(child);
  const parent = fixture.rows.find((row) => row.id === child.parent_id);
  assert.ok(parent);
  const sources = {
    child: child.source_urls[0],
    parent: parent.source_urls[0],
  };
  const builder = api.create(sources);
  const childTuple = definition(child);
  childTuple[1] = parent.name;
  builder.add(child.domain, child.family, "child", [childTuple]);
  builder.add(parent.domain, parent.family, "parent", [definition(parent)]);
  const rows = builder.complete();
  assert.deepEqual(
    rows.map((row) => row.id),
    [child.id, parent.id],
  );
  assert.equal(rows[0].parent_id, parent.id);
  assert.equal(rows[1].parent_id, null);
});
