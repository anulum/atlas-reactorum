// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original accessible rows and actual native selection.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm");
const { mount, classic } = require("./native-map-fixture.cjs");
const api = require("../accessibility.js");
test("complete original accessible list stays capped, identifies omitted records and emits the same source row", (context) => {
  /** @type {import("../../application-data.js").ApplicationFacility[]} */
  const selected = [];
  const { engine, canvas, rows, dom } = mount(context, {
    /**
     * Retain the actual original row emitted by native activation.
     * @param {import("../../application-data.js").ApplicationFacility} row Original selected source row.
     * @returns {number} Number of retained original emissions.
     */
    onSelect: (row) => selected.push(row),
  });
  engine.setData(rows);
  assert.equal(engine.points.length, 13357);
  assert.equal(engine.srList.children.length, 201);
  assert.ok(engine.srList.textContent?.includes("13157 records match"));
  const button = dom.window.document.querySelector("#mapHost button");
  assert.ok(button instanceof dom.window.HTMLButtonElement);
  button.click();
  assert.equal(selected[0], engine.points[0].row);
  assert.equal(engine.focus?.row, selected[0]);
  assert.equal(canvas.getAttribute("tabindex"), "0");
  engine.setData([]);
  assert.equal(engine.srList.children.length, 0);
});
test("actual absence of list/live-region state stays absent and supplied source text is retained", (context) => {
  const { engine, rows } = mount(context);
  engine.setData(rows.slice(0, 1));
  const list = engine.srList,
    status = engine.status;
  Reflect.set(engine, "srList", null);
  engine.renderAccessibleList();
  assert.equal(Reflect.get(engine, "srList"), null);
  Reflect.set(engine, "srList", list);
  Reflect.set(engine, "status", null);
  engine.announce("not announced");
  assert.equal(Reflect.get(engine, "status"), null);
  Reflect.set(engine, "status", status);
  engine.announce(rows[0].name);
  assert.equal(engine.status.textContent, rows[0].name);
  const row = { ...rows[0], name: null, country: null };
  const MapEngine = require("../engine.js");
  const nullable = new MapEngine({
    container: engine.container,
    document: engine.document,
  });
  nullable.setData([row]);
  assert.equal(
    nullable.srList.textContent,
    "Unnamed record — location not supplied",
  );
});
test("same actual classic API is loaded in a real DOM Window", (context) => {
  const { dom } = mount(context);
  classic(dom);
  const result = /** @type {unknown} */ (
    vm.runInContext(
      "AtlasMap.accessibility.LIST_LIMIT",
      dom.getInternalVMContext(),
    )
  );
  assert.equal(result, api.LIST_LIMIT);
});
