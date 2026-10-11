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

test("corrected captions preserve explicit original IDs and claim references", () => {
  const original = fixture.rows.find((row) => row.id === "phwr-candu");
  assert.ok(original);
  const tuple = definition(original);
  tuple[0] = "Pressure-tube PHWR including CANDU";
  tuple[8] = { id: original.id };
  const builder = api.create({ original: original.source_urls[0] });
  builder.add(original.domain, original.family, "original", [tuple]);
  const [row] = builder.complete();
  assert.equal(row.id, original.id);
  assert.equal(row.name, tuple[0]);
  const profile = fixture.document.records.find(
    (item) => item.entry_id === row.id,
  );
  assert.ok(profile);
  assert.ok(
    profile.claims.every((claim) => claim.claim_id.startsWith(row.id + ":")),
  );
});

test("explicit parent identity survives renamed captions and forward construction", () => {
  const child = fixture.rows.find((row) => row.parent_id !== null);
  assert.ok(child);
  const parent = fixture.rows.find((row) => row.id === child.parent_id);
  assert.ok(parent);
  const childTuple = definition(child);
  childTuple[0] = child.name + " revised";
  childTuple[1] = parent.name;
  childTuple[8] = { id: child.id, parent_id: parent.id };
  const parentTuple = definition(parent);
  parentTuple[0] = parent.name + " revised";
  parentTuple[8] = { id: parent.id, parent_id: null };
  const builder = api.create({ original: child.source_urls[0] });
  builder.add(child.domain, child.family, "original", [
    childTuple,
    parentTuple,
  ]);
  const rows = builder.complete();
  assert.equal(rows[0].parent_id, parent.id);
  assert.equal(rows[1].parent_id, null);
  assert.equal(builder.complete(), rows);
});

test("invalid or colliding explicit IDs and missing explicit parents refuse", () => {
  for (const id of [
    "",
    "Upper",
    "with space",
    "-leading",
    "trailing-",
    "double--dash",
  ]) {
    const tuple = definition(pwr);
    tuple[8] = { id };
    const builder = api.create({ original: pwr.source_urls[0] });
    assert.throws(
      () => builder.add(pwr.domain, pwr.family, "original", [tuple]),
      /stable identity is invalid/,
    );
    assert.deepEqual(builder.complete(), []);
  }
  const tuple = definition(pwr);
  tuple[8] = { id: pwr.id };
  const builder = api.create({ original: pwr.source_urls[0] });
  builder.add(pwr.domain, pwr.family, "original", [tuple]);
  assert.throws(
    () => builder.add(pwr.domain, pwr.family, "original", [tuple]),
    /Duplicate ID/,
  );
  assert.equal(builder.complete().length, 1);
  const dangling = api.create({ original: pwr.source_urls[0] });
  tuple[8] = { id: pwr.id, parent_id: "absent-parent" };
  dangling.add(pwr.domain, pwr.family, "original", [tuple]);
  assert.throws(() => dangling.complete(), /Missing parent/);
});

test("invalid explicit parent and nontextual JSON identities refuse without appending", () => {
  for (const overrides of [
    { id: null },
    { id: 4 },
    { id: false },
    { parent_id: "" },
    { parent_id: "Upper" },
    { parent_id: "two--dashes" },
    { parent_id: 4 },
    { parent_id: false },
  ]) {
    const tuple = definition(pwr);
    /** @type {unknown} Serialized invalid runtime input before constructor admission. */
    const incoming = JSON.parse(
      JSON.stringify([[...tuple.slice(0, 8), overrides]]),
    );
    const builder = api.create({ original: pwr.source_urls[0] });
    assert.throws(
      () =>
        Reflect.apply(builder.add, builder, [
          pwr.domain,
          pwr.family,
          "original",
          incoming,
        ]),
      /identity is invalid/,
    );
    assert.deepEqual(builder.complete(), []);
  }
  for (const overrides of [{ id: undefined }, { parent_id: undefined }]) {
    const builder = api.create({ original: pwr.source_urls[0] });
    const tuple = definition(pwr);
    tuple[8] = overrides;
    assert.throws(
      () => builder.add(pwr.domain, pwr.family, "original", [tuple]),
      /identity is invalid/,
    );
    assert.deepEqual(builder.complete(), []);
  }
});

test("only owned overrides bind identities and failed locators reserve no ID", () => {
  const builder = api.create({ original: pwr.source_urls[0] });
  const tuple = definition(pwr);
  tuple[8] = Object.create({
    id: "inherited-caption",
    parent_id: "missing-parent",
  });
  builder.add(pwr.domain, pwr.family, "original", [tuple]);
  assert.equal(builder.complete()[0].id, pwr.id);
  assert.equal(builder.complete()[0].parent_id, null);
  const retry = api.create({ original: pwr.source_urls[0] });
  tuple[8] = { id: pwr.id };
  assert.throws(
    () => retry.add(pwr.domain, pwr.family, "missing", [tuple]),
    /source identity is unavailable/,
  );
  retry.add(pwr.domain, pwr.family, "original", [tuple]);
  assert.equal(retry.complete().length, 1);
  assert.throws(
    () => retry.add(pwr.domain, pwr.family, "original", [definition(pwr)]),
    /Duplicate ID/,
  );
});

test("explicit parent absence survives a matching authored parent caption", () => {
  const child = fixture.rows.find((row) => row.parent_id !== null);
  assert.ok(child);
  const parent = fixture.rows.find((row) => row.id === child.parent_id);
  assert.ok(parent);
  const tuple = definition(child);
  tuple[1] = parent.name;
  tuple[8] = { parent_id: null };
  const builder = api.create({ original: child.source_urls[0] });
  builder.add(child.domain, child.family, "original", [
    tuple,
    definition(parent),
  ]);
  assert.equal(builder.complete()[0].parent_id, null);
});

test("classic browser construction preserves corrected caption identity and explicit parent", () => {
  const child = fixture.rows.find((row) => row.parent_id !== null);
  assert.ok(child);
  const parent = fixture.rows.find((row) => row.id === child.parent_id);
  assert.ok(parent);
  const childTuple = definition(child);
  childTuple[0] = child.name + " revised";
  childTuple[8] = { id: child.id, parent_id: parent.id };
  const parentTuple = definition(parent);
  parentTuple[0] = parent.name + " revised";
  parentTuple[8] = { id: parent.id, parent_id: null };
  const definitions = [childTuple, parentTuple];
  const sources = { original: child.source_urls[0] };
  const native = api.create(sources);
  native.add(child.domain, child.family, "original", definitions);
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
    /** @type {unknown} Actual classic browser result before the exact-value assertion. */
    const output = dom.window.eval(`{
      const builder = AtlasTaxonomyConstruction.create(${JSON.stringify(sources)});
      builder.add(${JSON.stringify(child.domain)}, ${JSON.stringify(child.family)}, "original", ${JSON.stringify(definitions)});
      JSON.stringify(builder.complete());
    }`);
    assert.equal(output, JSON.stringify(native.complete()));
  } finally {
    dom.window.close();
  }
});
