// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — engine integration with jsdom and Cairo canvas.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const MapEngine = require("../engine.js");

/**
 * Read the actual catalogue column set once for this integration module.
 * @returns {import("../engine.js").FacilityRow & Record<string, unknown>} First unchanged catalogue row.
 * @throws {Error} If the shipped catalogue envelope or required columns change.
 */
function readSourceRow() {
  /** @type {unknown} */
  const source = JSON.parse(
    fs.readFileSync(
      path.join(__dirname, "../../data/global_reactors.sample.json"),
      "utf8",
    ),
  );
  if (!source || typeof source !== "object" || !("records" in source)) {
    throw new Error("catalogue must contain records");
  }
  if (!Array.isArray(source.records) || source.records.length === 0) {
    throw new Error("catalogue records must be a nonempty array");
  }
  /** @type {unknown} */
  const first = source.records[0];
  if (!first || typeof first !== "object" || Array.isArray(first)) {
    throw new Error("catalogue record must be an object");
  }
  /** @type {Record<string, unknown>} */
  const template = Object.fromEntries(Object.entries(first));
  const { id, name, country, domain, lon, lat } = template;
  if (
    typeof id !== "string" ||
    typeof name !== "string" ||
    typeof country !== "string" ||
    typeof domain !== "string"
  ) {
    throw new Error("catalogue identity and display columns must be strings");
  }
  return { ...template, id, name, country, domain, lon, lat };
}

const sourceTemplate = readSourceRow();

/**
 * Clone the actual source column set with explicit interaction-case values.
 * @param {import("../engine.js").FacilityRow} overrides Fields varied by this case.
 * @returns {import("../engine.js").FacilityRow} Source-shaped row for the public engine.
 * @throws {Error} If a varied field is absent from the shipped column set.
 */
function sourceRow(overrides) {
  for (const key of Object.keys(overrides)) {
    if (!Object.hasOwn(sourceTemplate, key)) {
      throw new Error("catalogue is missing column " + key);
    }
  }
  return { ...sourceTemplate, ...overrides };
}

/**
 * Mount the real constructor in a DOM with a Cairo-backed canvas.
 * @param {import("node:test").TestContext} t Case owning window teardown.
 * @param {import("../engine.js").EngineOptions<import("../engine.js").FacilityRow>} [options] Public engine options; this function supplies the required host.
 * @param {boolean} [frames] Whether jsdom should expose its animation-frame implementation.
 * @returns {{dom:import("jsdom").JSDOM,engine:InstanceType<typeof MapEngine>,canvas:HTMLCanvasElement,ctx:CanvasRenderingContext2D}} Mounted components and their actual raster context.
 */
function mount(t, options = {}, frames = false) {
  const dom = new JSDOM("<!doctype html><div id='map'></div>", {
    pretendToBeVisual: frames,
  });
  t.after(
    /**
     * Close the DOM window and cancel its remaining timers.
     * @returns {void}
     */
    () => dom.window.close(),
  );
  const container = dom.window.document.getElementById("map");
  assert.ok(container);
  const engine = new MapEngine({ ...options, container });
  const canvas = container.querySelector("canvas");
  assert.ok(canvas);
  canvas.width = 960;
  canvas.height = 480;
  engine.viewport.resize(960, 480);
  const ctx = canvas.getContext("2d");
  assert.ok(ctx, "Cairo canvas backend is unavailable");
  return { dom, engine, canvas, ctx };
}

/**
 * Refuse nonfinite latitude and both negative geographic boundaries without creating points.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("invalid latitude and negative boundaries cannot enter the spatial index", (t) => {
  const { engine } = mount(t);
  const rows = [
    sourceRow({ lon: 0, lat: Infinity }),
    sourceRow({ lon: 0, lat: -Infinity }),
    sourceRow({ lon: 0, lat: "invalid" }),
    sourceRow({ lon: -180.01, lat: 0 }),
    sourceRow({ lon: 0, lat: -90.01 }),
  ];
  engine.setData(rows);
  assert.equal(engine.points.length, 0);
  assert.equal(engine.tree?.size, 0);
  assert.equal(engine.mapped, 0);
  assert.equal(engine.clusters.length, 0);
});

/**
 * Choose the nearer actual aggregate when neighbouring hit radii overlap.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("overlapping cluster hit radii choose the nearer drawn aggregate", (t) => {
  const { engine } = mount(t);
  /** @type {import("../engine.js").FacilityRow[]} */
  const rows = [];
  for (let i = 0; i < 20; i += 1) {
    rows.push(sourceRow({ lon: 0, lat: 0 }), sourceRow({ lon: 12, lat: 0 }));
  }
  engine.setData(rows);
  assert.equal(engine.clusters.length, 2);
  const [first, second] = engine.clusters;
  assert.equal(first.count, 20);
  assert.equal(second.count, 20);
  const middle = (first.x + second.x) / 2;
  const left = middle - 0.5;
  const right = middle + 0.5;
  assert.ok(Math.abs(second.x - left) < engine.radiusFor(second.count) + 4);
  assert.ok(Math.abs(first.x - right) < engine.radiusFor(first.count) + 4);
  assert.equal(engine.clusterAt(left, first.y), first);
  assert.equal(engine.clusterAt(right, second.y), second);
  assert.equal(engine.clusterAt(-1000, -1000), null);
});

/**
 * Detached native documents supply no Window; painting and positive sizing still work.
 * @param {import("node:test").TestContext} t Case owning the parent DOM window.
 * @returns {void}
 */
test("a detached native Document uses immediate painting and unit device ratio", (t) => {
  const { dom } = mount(t);
  const document =
    dom.window.document.implementation.createHTMLDocument("detached map");
  assert.equal(document.defaultView, null);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const engine = new MapEngine({ container, document });
  engine.resize();
  engine.setData([sourceRow({ lon: 0, lat: 0 })]);
  assert.equal(engine.document, document);
  assert.equal(engine.dpr, 1);
  assert.equal(engine.canvas.width, 1);
  assert.equal(engine.canvas.height, 1);
  assert.equal(engine.frame, null);
  assert.equal(engine.mapped, 1);
  assert.equal(engine.clusters[0].count, 1);
});

/**
 * Paint through the engine's actual index, aggregation and native raster backend.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("painting reports actual visible counts and fills the native canvas", (t) => {
  /** @type {import("../engine.js").ViewReport[]} */
  const views = [];
  const { engine, ctx } = mount(t, {
    /**
     * Retain reports emitted after the actual painting pipeline completes.
     * @param {import("../engine.js").ViewReport} view Just-painted record counts.
     * @returns {void}
     */
    onViewChange(view) {
      views.push(view);
    },
  });
  engine.draw();
  assert.deepEqual(views.pop(), {
    zoom: 1,
    visible: 0,
    clusters: 0,
    mapped: 0,
  });
  assert.deepEqual(
    Array.from(ctx.getImageData(1, 1, 1, 1).data),
    [16, 35, 31, 255],
  );
  const rows = [
    sourceRow({ lon: 0, lat: 0, name: "first", domain: "fusion" }),
    sourceRow({ lon: 0, lat: 0, name: "second", domain: "fission" }),
    sourceRow({ lon: null, lat: null, name: "unknown" }),
  ];
  engine.setData(rows);
  assert.deepEqual(views.pop(), {
    zoom: 1,
    visible: 2,
    clusters: 1,
    mapped: 2,
  });
  assert.equal(engine.clusters[0].count, 2);
  engine.focusPoint(engine.points[0]);
  assert.equal(engine.focusScreenEntry()?.count, 1);
  assert.equal(engine.focusScreenEntry()?.x, engine.viewport.width / 2);
  engine.setData(null);
  assert.equal(engine.focusScreenEntry(), null);
  assert.equal(engine.points.length, 0);
  engine.draw();
  assert.deepEqual(views.pop(), {
    zoom: 6,
    visible: 0,
    clusters: 0,
    mapped: 0,
  });
});

/**
 * Aggregate clicks zoom; individual and accessible activation preserve original rows.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("DOM clicks distinguish clusters, records and empty space", (t) => {
  /** @type {import("../engine.js").FacilityRow[]} */
  const selected = [];
  const { dom, engine, canvas } = mount(t, {
    /**
     * Retain the exact source identity supplied by the engine.
     * @param {import("../engine.js").FacilityRow} row Selected original record.
     * @returns {void}
     */
    onSelect(row) {
      selected.push(row);
    },
  });
  const rows = [sourceRow({ lon: 0, lat: 0 }), sourceRow({ lon: 0, lat: 0 })];
  engine.setData(rows);
  const entry = engine.clusters[0];
  assert.equal(engine.clusterAt(entry.x, entry.y), entry);
  canvas.dispatchEvent(
    new dom.window.MouseEvent("click", { clientX: entry.x, clientY: entry.y }),
  );
  assert.equal(engine.viewport.zoom, 2.5);
  assert.deepEqual(selected, []);
  engine.setData([rows[0]]);
  const point = engine.points[0];
  const screen = engine.viewport.toScreen(point.x, point.y);
  canvas.dispatchEvent(
    new dom.window.MouseEvent("click", {
      clientX: screen.x,
      clientY: screen.y,
    }),
  );
  assert.equal(selected[0], rows[0]);
  engine.activateAt(-1000, -1000);
  assert.equal(selected.length, 1);
  const button = dom.window.document.querySelector("button");
  assert.ok(button);
  button.click();
  assert.equal(selected.length, 2);
  assert.equal(selected[1], rows[0]);
  assert.equal(engine.focus, point);
  assert.equal(engine.viewport.zoom, 6);
});

/**
 * Repeated hover does not repaint, wheel cancellation and every key use DOM dispatch.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("DOM input pans, zooms, announces hover and preserves unhandled keys", (t) => {
  const { dom, engine, canvas } = mount(t);
  const row = sourceRow({
    lon: 0,
    lat: 0,
    name: "origin",
    country: "source country",
  });
  engine.setData([row]);
  engine.viewport.centreOn(0, 0, 8);
  engine.draw();
  const screen = engine.viewport.toScreen(
    engine.points[0].x,
    engine.points[0].y,
  );
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      clientX: screen.x,
      clientY: screen.y,
    }),
  );
  assert.equal(engine.focus?.row, row);
  assert.match(engine.status.textContent || "", /origin, source country/);
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      clientX: screen.x,
      clientY: screen.y,
    }),
  );
  assert.equal(engine.focus?.row, row);
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      clientX: -1000,
      clientY: -1000,
    }),
  );
  assert.equal(engine.focus, null);
  const wheel = new dom.window.WheelEvent("wheel", {
    clientX: 480,
    clientY: 240,
    deltaY: -120,
    cancelable: true,
  });
  const beforeWheel = engine.viewport.zoom;
  assert.equal(canvas.dispatchEvent(wheel), false);
  assert.equal(wheel.defaultPrevented, true);
  assert.ok(engine.viewport.zoom > beforeWheel);
  for (const key of [
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "+",
    "=",
    "-",
    "_",
    "0",
    "Enter",
    " ",
  ]) {
    const event = new dom.window.KeyboardEvent("keydown", {
      key,
      shiftKey: true,
      cancelable: true,
    });
    assert.equal(canvas.dispatchEvent(event), false, key);
  }
  const tab = new dom.window.KeyboardEvent("keydown", {
    key: "Tab",
    cancelable: true,
  });
  assert.equal(canvas.dispatchEvent(tab), true);
  engine.focusPoint(engine.points[0]);
  canvas.dispatchEvent(
    new dom.window.KeyboardEvent("keydown", { key: "Enter", cancelable: true }),
  );
  canvas.dispatchEvent(
    new dom.window.KeyboardEvent("keydown", { key: " ", cancelable: true }),
  );
  assert.equal(engine.focus?.row, row);
});

/**
 * Missing display fields stay explicit in both the accessible list and live region.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("absent names, countries and domains remain explicit during DOM activation", (t) => {
  const { dom, engine, canvas } = mount(t);
  const row = sourceRow({
    lon: 0,
    lat: 0,
    name: null,
    country: null,
    domain: null,
  });
  engine.setData([row]);
  assert.equal(engine.points[0].row, row);
  assert.equal(engine.points[0].domain, "unknown");
  const button = dom.window.document.querySelector("button");
  assert.ok(button);
  assert.equal(button.textContent, "Unnamed record — location not supplied");
  const point = engine.points[0];
  const screen = engine.viewport.toScreen(point.x, point.y);
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      clientX: screen.x,
      clientY: screen.y,
    }),
  );
  assert.equal(
    engine.status.textContent,
    "Unnamed record, location not supplied",
  );
  button.click();
  assert.equal(engine.focus?.row, row);
  assert.equal(row.name, null);
  assert.equal(row.country, null);
  assert.equal(row.domain, null);
});

/**
 * A cancelled gesture cannot select; a fresh gesture can, and a return drag stays a drag.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {void}
 */
test("DOM pointer cancellation and return drags suppress release clicks", (t) => {
  /** @type {import("../engine.js").FacilityRow[]} */
  const selected = [];
  const { dom, engine, canvas } = mount(t, {
    /**
     * Retain every row actually emitted by a deliberate activation.
     * @param {import("../engine.js").FacilityRow} row Original source identity.
     * @returns {void}
     */
    onSelect(row) {
      selected.push(row);
    },
  });
  const row = sourceRow({ lon: 0, lat: 0 });
  engine.setData([row]);
  engine.viewport.centreOn(0, 0, 8);
  engine.draw();
  const position = engine.viewport.toScreen(
    engine.points[0].x,
    engine.points[0].y,
  );
  const location = { clientX: position.x, clientY: position.y, pointerId: 7 };
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerdown", location));
  canvas.dispatchEvent(new dom.window.PointerEvent("pointercancel", location));
  canvas.dispatchEvent(new dom.window.MouseEvent("click", location));
  assert.deepEqual(selected, []);
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerdown", location));
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      ...location,
      clientX: position.x + 3,
    }),
  );
  canvas.dispatchEvent(new dom.window.PointerEvent("pointermove", location));
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerup", location));
  canvas.dispatchEvent(new dom.window.MouseEvent("click", location));
  assert.equal(selected[0], row);
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerdown", location));
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      ...location,
      clientX: position.x + 40,
    }),
  );
  canvas.dispatchEvent(new dom.window.PointerEvent("pointermove", location));
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerup", location));
  canvas.dispatchEvent(new dom.window.MouseEvent("click", location));
  assert.equal(selected.length, 1);
});

/**
 * Resize clamps absent DOM layout to positive dimensions; a frame batch emits one report.
 * @param {import("node:test").TestContext} t Case owning the DOM window.
 * @returns {Promise<void>} Completion after jsdom's real animation-frame callback.
 */
test("animation frames coalesce repaint requests and release their token", async (t) => {
  /** @type {import("../engine.js").ViewReport[]} */
  const views = [];
  const { dom, engine, canvas } = mount(
    t,
    {
      /**
       * Count actual completed paint reports, not scheduling requests.
       * @param {import("../engine.js").ViewReport} view Just-painted view state.
       * @returns {void}
       */
      onViewChange(view) {
        views.push(view);
      },
    },
    true,
  );
  engine.resize();
  assert.equal(canvas.width, 1);
  assert.equal(canvas.height, 1);
  assert.equal(canvas.style.width, "1px");
  assert.equal(canvas.style.height, "1px");
  const token = engine.frame;
  assert.notEqual(token, null);
  engine.requestDraw();
  engine.requestDraw();
  assert.equal(engine.frame, token);
  await new Promise(
    /**
     * Observe the next callback after the engine's already queued paint.
     * @param {(value?:undefined)=>void} resolve Promise completion callback.
     * @returns {number} Identifier of the queued observation frame.
     */
    (resolve) =>
      dom.window.requestAnimationFrame(
        /**
         * Release the observation after the animation frame runs.
         * @returns {void}
         */
        () => resolve(),
      ),
  );
  assert.equal(views.length, 1);
  assert.equal(engine.frame, null);
});
