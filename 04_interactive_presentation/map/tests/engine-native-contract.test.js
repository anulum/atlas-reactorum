// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — real native constructor, source, context and loading boundaries.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path"),
  vm = require("node:vm");
const { mount, classic } = require("./native-map-fixture.cjs");
const MapEngine = require("../engine.js");
test("absent options/container/document refuse through the actual constructor", (context) => {
  const { dom } = mount(context);
  assert.throws(() => new MapEngine(), /container element is required/);
  assert.throws(() => new MapEngine(null), /container element is required/);
  assert.throws(
    () => new MapEngine({ container: dom.window.document }),
    /document is required/,
  );
});
test("original complete row coordinate control rejects absent, blank and invalid longitude/latitude", (context) => {
  const { rows } = mount(context),
    source = rows[0];
  for (const fields of [
    { lon: undefined },
    { lat: undefined },
    { lon: true },
    { lat: false },
    { lon: "" },
    { lon: " " },
    { lat: "" },
    { lat: " " },
    { lon: "invalid" },
    { lat: "invalid" },
    { lon: NaN },
    { lat: Infinity },
    { lon: -181 },
    { lon: 181 },
    { lat: -91 },
    { lat: 91 },
  ])
    assert.equal(MapEngine.coordinatesOf({ ...source, ...fields }), null);
  assert.deepEqual(MapEngine.coordinatesOf({ ...source, lon: "0", lat: "0" }), {
    lon: 0,
    lat: 0,
  });
});
test("a genuine DOM with its optional raster capability absent remains usable", (context) => {
  const { dom } = mount(context);
  const prototype = dom.window.HTMLCanvasElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(prototype, "getContext");
  assert.ok(descriptor);
  assert.equal(Reflect.deleteProperty(prototype, "getContext"), true);
  try {
    const container = dom.window.document.createElement("div");
    dom.window.document.body.appendChild(container);
    const engine = new MapEngine({ container });
    assert.equal(engine.ctx, null);
    engine.setData([]);
    engine.draw();
    assert.equal(engine.points.length, 0);
    assert.equal(container.querySelector("canvas"), engine.canvas);
  } finally {
    Object.defineProperty(prototype, "getContext", descriptor);
  }
});
test("actual fragment containers use the documented geometry fallback and absent raster/index remain inert", (context) => {
  const { dom } = mount(context);
  const fragment = dom.window.document.createDocumentFragment();
  const engine = new MapEngine({ container: fragment });
  engine.resize();
  assert.equal(engine.viewport.width, 960);
  assert.equal(engine.viewport.height, 480);
  assert.equal(engine.focusScreenEntry(), null);
  assert.equal(engine.pointAt(0, 0), null);
  const raster = engine.ctx;
  engine.ctx = null;
  engine.draw();
  assert.equal(engine.ctx, null);
  engine.ctx = raster;
  engine.draw();
});
test("missing namespace and every omitted real classic dependency refuse without publishing a constructor", (context) => {
  const { dom } = mount(context),
    filename = path.resolve(__dirname, "../engine.js"),
    code = fs.readFileSync(filename, "utf8"),
    ctx = dom.getInternalVMContext();
  assert.throws(
    () => vm.runInContext(code, ctx, { filename }),
    /load all map modules before engine.js/,
  );
  classic(dom, ["engine"]);
  for (const name of [
    "projection",
    "coastline",
    "Quadtree",
    "cluster",
    "Viewport",
    "renderer",
    "interactions",
    "accessibility",
  ]) {
    const removed = vm.runInContext("AtlasMap." + name, ctx);
    vm.runInContext("delete AtlasMap." + name, ctx);
    assert.throws(
      () => vm.runInContext(code, ctx, { filename }),
      /load all map modules before engine.js/,
    );
    assert.equal(vm.runInContext("AtlasMap.MapEngine", ctx), undefined);
    Reflect.set(dom.window.AtlasMap, name, removed);
  }
});
test("new actual helper classic namespaces can load independently into a genuine fresh Window", (context) => {
  for (const name of ["interactions", "accessibility"]) {
    const { dom } = mount(context),
      filename = path.resolve(__dirname, "../" + name + ".js");
    vm.runInContext(
      fs.readFileSync(filename, "utf8"),
      dom.getInternalVMContext(),
      { filename },
    );
    const found = /** @type {unknown} */ (
      vm.runInContext("typeof AtlasMap." + name, dom.getInternalVMContext())
    );
    assert.equal(found, "object");
  }
});
