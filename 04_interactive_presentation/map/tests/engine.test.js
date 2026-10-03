// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — map engine tests over a minimal DOM stub.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const MapEngine = require("../engine.js");

const DATA = path.join(__dirname, "..", "..", "data", "global_reactors.sample.json");

/**
 * Minimal element stub sufficient for the engine's DOM usage.
 *
 * @param {string} tag Tag name.
 * @returns {object} The element stub.
 */
function makeElement(tag) {
  return {
    tagName: tag,
    children: [],
    listeners: {},
    style: {},
    attributes: {},
    textContent: "",
    firstChild: null,
    className: "",
    type: "",
    ownerDocument: null,
    setAttribute(k, v) {
      this.attributes[k] = v;
    },
    getAttribute(k) {
      return this.attributes[k];
    },
    appendChild(child) {
      this.children.push(child);
      this.firstChild = this.children[0];
      return child;
    },
    removeChild(child) {
      this.children = this.children.filter((c) => c !== child);
      this.firstChild = this.children[0] || null;
      return child;
    },
    addEventListener(name, fn) {
      (this.listeners[name] = this.listeners[name] || []).push(fn);
    },
    getBoundingClientRect() {
      return { width: 960, height: 480, left: 0, top: 0 };
    },
    getContext() {
      return null;
    },
  };
}

/**
 * Document stub wiring elements to a fake window.
 *
 * @returns {object} The document stub.
 */
function makeDocument() {
  const doc = {
    defaultView: { devicePixelRatio: 2, requestAnimationFrame: null },
    createElement: (tag) => {
      const el = makeElement(tag);
      el.ownerDocument = doc;
      return el;
    },
  };
  return doc;
}

/**
 * Build an engine over a container stub.
 *
 * @param {object} [options] Extra engine options.
 * @returns {{engine: MapEngine, container: object}} Engine and container.
 */
function makeEngine(options) {
  const doc = makeDocument();
  const container = doc.createElement("div");
  const engine = new MapEngine(
    Object.assign(
      {
        container,
        document: doc,
        rings: [[[0, 0], [10, 0], [10, 10]]],
      },
      options || {},
    ),
  );
  return { engine, container };
}

/** Load the shipped facility records. */
function realRows() {
// Datasets are published as a document whose `records` array carries the
// rows; older exports were bare arrays. Accept both, so the tests read the
// real shipped file whichever form it is in.
  const document = JSON.parse(fs.readFileSync(DATA, "utf8"));
  return Array.isArray(document) ? document : document.records;
}

test("a container is required", () => {
  assert.throws(() => new MapEngine({}), /container element is required/);
});

test("records without usable coordinates are rejected, never invented", () => {
  // Coercing a missing coordinate to zero would place the record in the Gulf
  // of Guinea — a location no source ever supplied.
  const bad = [
    { lon: "", lat: "" },
    { lon: null, lat: 5 },
    { lon: 5, lat: null },
    { lon: undefined, lat: undefined },
    { lon: "abc", lat: "5" },
    { lon: 200, lat: 5 },
    { lon: 5, lat: 100 },
    { lon: NaN, lat: NaN },
    {},
  ];
  for (const row of bad) {
    assert.equal(MapEngine.coordinatesOf(row), null, JSON.stringify(row));
  }
  assert.deepEqual(MapEngine.coordinatesOf({ lon: "12.5", lat: "-3.25" }), {
    lon: 12.5,
    lat: -3.25,
  });
  assert.deepEqual(MapEngine.coordinatesOf({ lon: 0, lat: 0 }), { lon: 0, lat: 0 });
});

test("the engine exposes canvas, accessible list and live region", () => {
  const { engine, container } = makeEngine();
  assert.equal(container.children.length, 3);
  assert.equal(engine.canvas.tagName, "canvas");
  assert.equal(engine.canvas.getAttribute("tabindex"), "0");
  assert.ok(engine.canvas.getAttribute("aria-label").length > 40);
  assert.equal(engine.srList.tagName, "ul");
  assert.equal(engine.status.getAttribute("aria-live"), "polite");
});

test("the keyboard path never disappears as the dataset grows", () => {
  // The previous SVG map set tabindex to -1 above 500 rows, silently removing
  // keyboard access exactly when the dataset was complete. Assert the
  // opposite: focusable entries exist at full dataset size.
  const { engine } = makeEngine();
  engine.setData(realRows());
  assert.ok(engine.points.length > 12000, "expected the full dataset");
  const buttons = engine.srList.children.filter((li) =>
    li.children.some((c) => c.tagName === "button"),
  );
  assert.ok(buttons.length > 0, "no focusable records exposed");
  assert.equal(engine.canvas.getAttribute("tabindex"), "0", "canvas lost keyboard focus");
});

test("the accessible list says how many records it could not list", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  const last = engine.srList.children[engine.srList.children.length - 1];
  assert.match(last.textContent, /A further \d+ records match/);
});

test("projecting the real dataset keeps every mappable record", () => {
  const rows = realRows();
  const { engine } = makeEngine();
  engine.setData(rows);
  const expected = rows.filter((r) => MapEngine.coordinatesOf(r) !== null).length;
  assert.equal(engine.points.length, expected);
  assert.equal(engine.mapped, expected);
  assert.ok(expected > 12000, `only ${expected} records were mappable`);
});

test("switching projection re-projects without losing records", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  const before = engine.points.length;
  const firstX = engine.points[0].x;
  engine.setProjection("plate-carree");
  assert.equal(engine.points.length, before, "records lost on reprojection");
  assert.notEqual(engine.points[0].x, firstX, "coordinates did not actually change");
  assert.equal(engine.projection.id, "plate-carree");
});

test("an unknown projection is rejected rather than silently ignored", () => {
  const { engine } = makeEngine();
  assert.throws(() => engine.setProjection("mercator"), /unknown projection/);
});

test("hit testing finds a known record at its own screen position", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  engine.viewport.resize(960, 480);
  const target = engine.points[0];
  engine.viewport.centreOn(target.x, target.y, 8);
  const screen = engine.viewport.toScreen(target.x, target.y);
  const hit = engine.pointAt(screen.x, screen.y);
  assert.ok(hit, "no record found at its own position");
  assert.equal(hit.row.id, target.row.id);
});

test("hit testing empty space returns nothing", () => {
  const { engine } = makeEngine();
  engine.setData([{ lon: 0, lat: 0, name: "origin", domain: "fission" }]);
  engine.viewport.resize(960, 480);
  assert.equal(engine.pointAt(-500, -500), null);
});

test("selection is emitted with the original source row", () => {
  let received = null;
  const { engine } = makeEngine({ onSelect: (row) => { received = row; } });
  const row = { lon: 10, lat: 20, name: "Test site", domain: "fusion", id: "x1" };
  engine.setData([row]);
  engine.emitSelection(engine.points[0]);
  assert.equal(received, row, "the caller must receive the untouched source row");
});

test("keyboard panning, zooming and reset all respond", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  engine.viewport.resize(960, 480);
  engine.viewport.zoom = 8;
  engine.viewport.clampCentre();
  const prevented = [];
  const press = (key) => {
    engine.handleKey({ key, shiftKey: false, preventDefault: () => prevented.push(key) });
  };
  const startX = engine.viewport.centreX;
  press("ArrowRight");
  assert.notEqual(engine.viewport.centreX, startX, "arrow key did not pan");
  const zoom = engine.viewport.zoom;
  press("+");
  assert.ok(engine.viewport.zoom > zoom, "plus did not zoom in");
  press("-");
  press("0");
  assert.equal(engine.viewport.zoom, engine.viewport.minZoom, "zero did not reset");
  assert.ok(prevented.length >= 4, "handled keys must prevent default scrolling");
});

test("unhandled keys are left alone for the browser", () => {
  const { engine } = makeEngine();
  let prevented = false;
  engine.handleKey({ key: "Tab", preventDefault: () => { prevented = true; } });
  assert.equal(prevented, false, "Tab must remain available for focus movement");
});

test("activating a record announces it to assistive technology", () => {
  const { engine } = makeEngine();
  engine.setData([{ lon: 10, lat: 20, name: "Announced site", country: "Nowhere", domain: "fusion" }]);
  engine.viewport.resize(960, 480);
  const screen = engine.viewport.toScreen(engine.points[0].x, engine.points[0].y);
  engine.setFocusFromScreen(screen.x, screen.y);
  assert.match(engine.status.textContent, /Announced site/);
  assert.match(engine.status.textContent, /Nowhere/);
});

test("a record with no name or country still announces something useful", () => {
  const { engine } = makeEngine();
  engine.setData([{ lon: 10, lat: 20, domain: "fusion" }]);
  engine.viewport.resize(960, 480);
  const screen = engine.viewport.toScreen(engine.points[0].x, engine.points[0].y);
  engine.setFocusFromScreen(screen.x, screen.y);
  assert.match(engine.status.textContent, /Unnamed record/);
  assert.match(engine.status.textContent, /location not supplied/);
});

test("an empty dataset leaves the engine usable", () => {
  const { engine } = makeEngine();
  engine.setData([]);
  assert.equal(engine.points.length, 0);
  assert.equal(engine.pointAt(10, 10), null);
  assert.equal(engine.srList.children.length, 0);
});
