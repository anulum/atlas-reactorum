// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original research field source rendering conformance
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const file = path.join(root, "04_interactive_presentation/facility-source-assertions.js");
const api = require(file);
const records = JSON.parse(fs.readFileSync(path.join(root, "04_interactive_presentation/data/global_reactors.sample.json"), "utf8")).records;
const original = records.flatMap(row => row.research_field_origins || []);

test("every actual accepted assertion keeps its source meaning and original bytes", () => {
  assert.ok(original.some(origin => origin.field === "first_criticality"));
  assert.ok(original.some(origin => origin.selection === "superseded"));
  for (const row of records) {
    const origins = row.research_field_origins || [];
    const html = api.render(origins);
    assert.equal(html === "", origins.length === 0);
    for (const origin of origins) {
      assert.ok(html.includes(origin.source_sha256));
      assert.ok(html.includes(origin.source_dataset));
      assert.ok(html.includes(origin.selection === "selected" ? "Selected value" : "Previous source assertion"));
    }
  }
});

test("browser script exports the same real renderer", () => {
  const context = {URL};
  vm.runInNewContext(fs.readFileSync(file, "utf8"), context, {filename: file});
  assert.equal(context.FacilitySourceAssertions.render(original), api.render(original));
});

test("malformed actual assertions refuse without interpreter or URL diagnostics", () => {
  const refusal = '<p role="status">Research field sources are unavailable.</p>';
  for (const value of [null, {}, "unbound original", [null], [true], [{...original[0], extra: "unbound"}]]) assert.equal(api.render(value), refusal);
  for (const field of Object.keys(original[0])) assert.equal(api.render([{...original[0], [field]: null}]), refusal);
  for (const change of [{field: "unbound field"}, {value: ""}, {source_sha256: "changed"}, {selection: "unreviewed"}, {source_dataset: ""}]) assert.equal(api.render([{...original[0], ...change}]), refusal);
  for (const source_url of ["javascript:alert(1)", "http://example.org/", "https://user@example.org/", "https://user:secret@example.org/", "https://:secret@example.org/", "https:///no-host", "https://[invalid/", "relative/source"]) assert.equal(api.render([{...original[0], source_url}]), refusal);
});

test("source text remains text and absent metadata stays explicitly unknown", () => {
  const row = {...original[0], value: "<&>\"'", source_role: "", source_capture_date: "", license: "", scope: ""};
  const html = api.render([row]);
  assert.ok(html.includes("&lt;&amp;&gt;&quot;&#39;"));
  assert.ok(html.includes("Source role not specified"));
  assert.ok(html.includes("date unknown"));
  assert.ok(html.includes("Source rights not specified"));
  assert.ok(html.includes("Source scope not specified"));
  assert.ok(!html.includes("<&>"));
});
