// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility_export.test.cjs
"use strict";

const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm");
const {
  actualPage,
  originalDocument,
  loadScripts,
} = require("./catalogue_dom_fixture.cjs");
require("../04_interactive_presentation/application-data.js");
const admission = globalThis.AtlasApplicationData;
const api = require("../04_interactive_presentation/facility-export.js");
const rows = admission.facilities(originalDocument("global_reactors.sample"));
test("complete JSON export retains all13459 source records, ordering and every unknown producer cell", () => {
  const before = JSON.stringify(rows);
  const encoded = api.serialize(rows, "json");
  assert.ok(encoded.endsWith("\n"));
  assert.deepEqual(JSON.parse(encoded), rows);
  assert.equal(JSON.stringify(rows), before);
});
test("complete CSV uses the original22 columns and quotes retained nested source arrays", () => {
  const encoded = api.serialize(rows, "csv");
  assert.ok(
    encoded.startsWith(
      "id,name,country,domain,record_kind,type,status,lat,lon,operator,organization,purpose,process_or_activity,fuel_or_feed,first_criticality,research_field_origins,research_primary_assertions,field_observations,source_urls,source_url,dataset_source,data_caveat\n",
    ),
  );
  const row = rows.find((value) => value.field_observations?.length);
  assert.ok(row?.field_observations);
  assert.ok(
    encoded.includes(
      JSON.stringify(row.field_observations).replaceAll('"', '""'),
    ),
  );
  assert.ok(encoded.endsWith("\n"));
});
test("real classic-script and native export consumers return identical whole JSON bytes", (context) => {
  const dom = actualPage(context);
  loadScripts(dom, [
    "application-data.js",
    "data/global_reactors.sample.js",
    "facility-export.js",
  ]);
  const output = /** @type {unknown} */ (
    vm.runInContext(
      "AtlasFacilityExport.serialize(AtlasApplicationData.facilities(REACTOR_FACILITIES),'json')",
      dom.getInternalVMContext(),
    )
  );
  assert.equal(output, api.serialize(rows, "json"));
});
test("empty filtered export keeps its format and no original records are inserted", () => {
  assert.equal(api.serialize([], "json"), "[]\n");
  assert.equal(api.serialize([], "csv").split("\n").length, 2);
});
