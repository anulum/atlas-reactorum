// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original dataset admission and malformed public inputs.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");
require("../04_interactive_presentation/application-data.js");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
const api = globalThis.AtlasApplicationData;
const root = path.resolve(__dirname, "..");
const fixture = loadProfileFixture(root);
const taxonomy = fixture.rows;

/**
 * Read complete original released input without giving unchecked JSON a row type.
 * @param {string} name Actual released dataset basename.
 * @returns {unknown} Original generated document cells.
 */
function document(name) {
  return /** @type {unknown} */ (
    JSON.parse(
      fs.readFileSync(
        path.join(root, "04_interactive_presentation/data", name + ".json"),
        "utf8",
      ),
    )
  );
}

test("all original datasets retain every cell, row identity, ordering and source object", () => {
  /** @type {[unknown, (input:unknown)=>unknown[], number][]} */
  const cases = [
    [document("global_reactors.sample"), api.facilities, 13459],
    [document("fusion_companies.sample"), api.companies, 98],
    [document("anulum_reactor_repos"), api.repositories, 30],
    [document("taxonomy-audit"), api.audits, 135],
  ];
  for (const [input, read, count] of cases) {
    assert.ok(input && typeof input === "object" && "records" in input);
    const before = JSON.stringify(input);
    const original = input.records;
    assert.equal(read(input), original);
    assert.equal(read(original).length, count);
    assert.equal(JSON.stringify(input), before);
  }
  assert.equal(api.taxonomy(taxonomy), taxonomy);
  assert.equal(taxonomy.length, 135);
});

test("explicit dataset absence retains empty collections without invented source records", () => {
  for (const read of Object.values(api)) {
    assert.deepEqual(read(undefined), []);
    assert.deepEqual(read(null), []);
    assert.deepEqual(read([]), []);
    assert.deepEqual(read({ records: [] }), []);
  }
});

test("present malformed documents, rows and declared counts refuse through public readers", () => {
  for (const input of [
    false,
    12,
    "unavailable",
    {},
    { records: {} },
    { records: null },
    Object.create({ records: [] }),
  ]) {
    assert.throws(() => api.facilities(input), /Atlas dataset/);
  }
  for (const count of [true, "0", 0.5, -1, 1]) {
    assert.throws(
      () => api.facilities({ records: [], record_count: count }),
      /record count differs/,
    );
  }
  for (const row of [undefined, null, false, 12, "record", []]) {
    assert.throws(() => api.companies([row]), /record must be an object/);
  }
});

test("required owned text and optional consumed strings cannot acquire invented values", () => {
  const original = api.companies(document("fusion_companies.sample"))[0];
  /** @type {Record<string,unknown>} */
  const missing = structuredClone(original);
  delete missing.name;
  assert.throws(
    () => api.companies([missing]),
    /text cell is unavailable: name/,
  );
  const inherited = Object.create({ name: original.name });
  Object.assign(inherited, missing);
  assert.throws(
    () => api.companies([inherited]),
    /text cell is unavailable: name/,
  );
  for (const field of ["name", "independent_source_url"]) {
    /** @type {Record<string,unknown>} */
    const damaged = structuredClone(original);
    damaged[field] = { unavailable: true };
    assert.throws(() => api.companies([damaged]), /text cell is unavailable/);
  }
  /** @type {Record<string,unknown>} */
  const absent = structuredClone(original);
  delete absent.independent_source_url;
  delete absent.source_urls;
  assert.equal(api.companies([absent])[0], absent);
});

test("optional producer cells stay unknown and complete observations retain original source bindings", () => {
  const original = api.facilities(document("global_reactors.sample"));
  const row = original.find((record) => record.field_observations);
  assert.ok(row);
  assert.ok(row.field_observations);
  /** @type {Record<string,unknown>} */
  const candidate = structuredClone(row);
  candidate.unreviewed_extra = { state: "unknown", nested: [null, false] };
  candidate.field_observations = [];
  delete candidate.record_kind;
  delete candidate.dataset_source;
  const before = JSON.stringify(candidate);
  assert.equal(api.facilities([candidate])[0], candidate);
  assert.equal(JSON.stringify(candidate), before);
  for (const observations of [
    {},
    [null],
    [{ ...row.field_observations[0], basis: 17 }],
  ]) {
    assert.throws(
      () => api.facilities([{ ...row, field_observations: observations }]),
      /Atlas/,
    );
  }
});

test("facility coordinate types, finite values and schema ranges refuse without coercion", () => {
  const original = api.facilities(document("global_reactors.sample"))[0];
  for (const [field, value] of [
    ["lat", undefined],
    ["lat", ""],
    ["lat", NaN],
    ["lat", Infinity],
    ["lat", 91],
    ["lon", -181],
  ]) {
    assert.throws(
      () => api.facilities([{ ...original, [String(field)]: value }]),
      /coordinate is unavailable/,
    );
  }
  const boundary = { ...original, lat: -90, lon: 180 };
  assert.equal(api.facilities([boundary])[0], boundary);
  const unknown = { ...original, lat: null, lon: null };
  assert.equal(api.facilities([unknown])[0], unknown);
});

test("source and topic lists retain original text and reject malformed cells", () => {
  const company = api.companies(document("fusion_companies.sample"))[0];
  const repository = api.repositories(document("anulum_reactor_repos"))[0];
  for (const value of [null, {}, "source", [null], [17]]) {
    assert.throws(
      () => api.companies([{ ...company, source_urls: value }]),
      /text array is unavailable/,
    );
    assert.throws(
      () => api.repositories([{ ...repository, topics: value }]),
      /text array is unavailable/,
    );
  }
  assert.equal(api.repositories([{ ...repository, topics: [] }]).length, 1);
});

test("taxonomy parent, reference and scalar cells remain source values and refuse malformed input", () => {
  const row = taxonomy[0];
  for (const [field, value] of [
    ["parent_id", false],
    ["scale", "not_reported"],
    ["control", NaN],
    ["source_ids", {}],
    ["source_urls", [17]],
  ]) {
    assert.throws(
      () => api.taxonomy([{ ...row, [String(field)]: value }]),
      /Atlas/,
    );
  }
  const finite = {
    ...row,
    scale: 0,
    control: 1,
  };
  assert.equal(api.taxonomy([finite])[0], finite);
  assert.throws(
    () =>
      globalThis.AtlasTaxonomyEvidenceProfiles.render(
        fixture.document,
        fixture.document.inputs.taxonomy_sha256,
        finite,
      ),
    /Evidence profile taxonomy context differs/,
  );
  assert.equal(api.taxonomy([{ ...row, parent_id: null }]).length, 1);
});

test("historical audit cells refuse changed shapes while preserving empty original locators", () => {
  const row = api.audits(document("taxonomy-audit"))[0];
  assert.throws(
    () => api.audits([{ ...row, classification_ok: null }]),
    /text cell is unavailable/,
  );
  const missingLocator = { ...row, verified_source_url: "" };
  assert.equal(api.audits([missingLocator])[0], missingLocator);
});
