// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility_field_sources.test.cjs
"use strict";

const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm");
const {
  actualPage,
  originalDocument,
  loadScripts,
} = require("./catalogue_dom_fixture.cjs");
require("../04_interactive_presentation/presentation-text.js");
require("../04_interactive_presentation/application-data.js");
const admission = globalThis.AtlasApplicationData;
const api = require("../04_interactive_presentation/facility-field-sources.js");
const rows = admission.facilities(originalDocument("global_reactors.sample"));
test("every original observation retains its value, capture date, column and rights in actual native HTML", () => {
  let observed = 0;
  const before = JSON.stringify(rows);
  for (const row of rows) {
    const html = api.render(row);
    if (!row.field_observations?.length) {
      assert.equal(html, "");
      continue;
    }
    observed += row.field_observations.length;
    for (const observation of row.field_observations) {
      assert.ok(
        html.includes(
          globalThis.AtlasPresentationText.escape(observation.value),
        ),
      );
      assert.ok(html.includes(observation.checked));
      assert.ok(html.includes(observation.source_field));
      assert.ok(html.includes(observation.license));
    }
  }
  assert.equal(observed, 1631);
  assert.equal(JSON.stringify(rows), before);
});
test("actual classic-script consumer agrees with native serialization without a fabricated Window", (context) => {
  const dom = actualPage(context);
  loadScripts(dom, [
    "presentation-text.js",
    "application-data.js",
    "data/global_reactors.sample.js",
    "facility-field-sources.js",
  ]);
  const output = /** @type {unknown} */ (
    vm.runInContext(
      "AtlasFacilityFieldSources.render(AtlasApplicationData.facilities(REACTOR_FACILITIES).find(row=>row.field_observations?.length))",
      dom.getInternalVMContext(),
    )
  );
  const row = rows.find((value) => value.field_observations?.length);
  assert.ok(row);
  assert.equal(output, api.render(row));
});
test("changed source text remains text and original absent observation does not acquire one", () => {
  const original = rows.find((row) => row.field_observations?.length);
  assert.ok(original?.field_observations);
  const changed = {
    ...original,
    field_observations: original.field_observations.map((row) => ({
      ...row,
      value: row.value + " <script>owned source control</script>",
    })),
  };
  assert.ok(!api.render(changed).includes("<script>"));
  assert.ok(api.render(changed).includes("&lt;script&gt;"));
  assert.equal(api.render({ ...original, field_observations: [] }), "");
});
