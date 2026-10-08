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
const vm = require("node:vm");
const MapEngine = require("../engine.js");
require("../../application-data.js");

/**
 * Existing DOM-like unit adapter; it records listeners and supplies no rendering context.
 * @typedef {object} TestElement
 * @property {string} tagName Supplied lower-case tag name.
 * @property {TestElement[]} children Appended child elements in order.
 * @property {Record<string, unknown[]>} listeners Retained event callbacks, without invoking them.
 * @property {{width?:string,height?:string}} style Assigned CSS size fields.
 * @property {Record<string,string>} attributes Assigned attributes.
 * @property {string} textContent Current authored text.
 * @property {TestElement|null} firstChild First retained child, or null.
 * @property {string} className Assigned class list.
 * @property {string} type Assigned button type.
 * @property {TestDocument|null} ownerDocument Owning adapter document, when wired.
 * @property {(k:string,v:string)=>void} setAttribute Attribute assignment.
 * @property {(k:string)=>string|undefined} getAttribute Recorded attribute lookup.
 * @property {(child:TestElement)=>TestElement} appendChild Child insertion.
 * @property {(child:TestElement)=>TestElement} removeChild Child removal by identity.
 * @property {(name:string,fn:unknown)=>void} addEventListener Listener retention, without dispatch.
 * @property {()=>{width:number,height:number,left:number,top:number}} getBoundingClientRect Fixed adapter geometry.
 * @property {()=>null} getContext No raster context; real Chrome supplies browser evidence separately.
 */

/**
 * Existing document adapter exposing only element creation and a fixed device ratio.
 * @typedef {{defaultView:{devicePixelRatio:number,requestAnimationFrame:null},createElement:(tag:string)=>TestElement}} TestDocument
 */

const DATA = path.join(
  __dirname,
  "..",
  "..",
  "data",
  "global_reactors.sample.json",
);

/**
 * Minimal element stub sufficient for the engine's DOM usage.
 * @param {string} tag Tag name.
 * @returns {TestElement} Existing call/state adapter; this is not a native DOM element.
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
    /**
     * Retain a named attribute exactly as supplied by the real map constructor.
     * @param {string} k Attribute name.
     * @param {string} v Attribute value.
     * @returns {void}
     */
    setAttribute(k, v) {
      this.attributes[k] = v;
    },
    /**
     * Read an assigned attribute without inventing a default.
     * @param {string} k Attribute name.
     * @returns {string|undefined} Stored value, or undefined when absent.
     */
    getAttribute(k) {
      return this.attributes[k];
    },
    /**
     * Append a supplied element by identity and update the first-child view.
     * @param {TestElement} child Actual child produced by this adapter document.
     * @returns {TestElement} The same appended child.
     */
    appendChild(child) {
      this.children.push(child);
      this.firstChild = this.children[0];
      return child;
    },
    /**
     * Remove one supplied child identity and refresh the first-child view.
     * @param {TestElement} child Child selected by the map's list-clearing loop.
     * @returns {TestElement} The same requested child.
     */
    removeChild(child) {
      this.children = this.children.filter(
        /**
         * Retain children whose identities differ from the removed one.
         * @param {TestElement} c Existing child.
         * @returns {boolean} Whether the child remains.
         */
        (c) => c !== child,
      );
      this.firstChild = this.children[0] || null;
      return child;
    },
    /**
     * Retain heterogeneous event callbacks without executing or retyping them.
     * @param {string} name Event name.
     * @param {unknown} fn Supplied callback whose native event shape is owned by the engine.
     * @returns {void}
     */
    addEventListener(name, fn) {
      (this.listeners[name] = this.listeners[name] || []).push(fn);
    },
    /**
     * Return the existing fixed container geometry used by the unit cases.
     * @returns {{width:number,height:number,left:number,top:number}} CSS-pixel geometry.
     */
    getBoundingClientRect() {
      return { width: 960, height: 480, left: 0, top: 0 };
    },
    /**
     * Expose that this adapter cannot paint canvas pixels.
     * @returns {null} No rendering context.
     */
    getContext() {
      return null;
    },
  };
}

/**
 * Document stub wiring elements to a fake window.
 * @returns {TestDocument} Adapter with immediate redraw fallback and no canvas rasterisation.
 */
function makeDocument() {
  /** @type {TestDocument} */
  const doc = {
    defaultView: { devicePixelRatio: 2, requestAnimationFrame: null },
    /**
     * Create and wire one existing element adapter to this document.
     * @param {string} tag Requested tag.
     * @returns {TestElement} Child retaining this document's identity.
     */
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
 * @param {import("../engine.js").EngineOptions<import("../engine.js").FacilityRow>} [options] Actual constructor options over the existing unit adapter.
 * @returns {{engine:InstanceType<typeof import("../engine.js")>,container:TestElement}} Actual map engine and its adapter container.
 */
function makeEngine(options) {
  const doc = makeDocument();
  const container = doc.createElement("div");
  const engine = new MapEngine(
    Object.assign(
      {
        container,
        document: doc,
        rings: [
          [
            [0, 0],
            [10, 0],
            [10, 10],
          ],
        ],
      },
      options || {},
    ),
  );
  return { engine, container };
}

/**
 * Read the shipped, producer-validated facility document and retain its original records.
 * @returns {import("../engine.js").FacilityRow[]} Original generated source rows; legacy bare arrays remain readable.
 * @throws {Error} A consumed original dataset cell or coordinate fails public admission.
 */
function realRows() {
  // Datasets are published as a document whose `records` array carries the
  // rows; older exports were bare arrays. Accept both, so the tests read the
  // real shipped file whichever form it is in.
  /** @type {unknown} */
  const document = JSON.parse(fs.readFileSync(DATA, "utf8"));
  return globalThis.AtlasApplicationData.facilities(document);
}

/**
 * Verify the real constructor refuses absent container options before mounting anything.
 * @returns {void}
 */
test("a container is required", () => {
  assert.throws(
    /**
     * Invoke the actual constructor without its required container.
     * @returns {InstanceType<typeof import("../engine.js")>} A constructed instance only if the required refusal is broken.
     */
    () => new MapEngine({}),
    /container element is required/,
  );
});

/**
 * Verify coordinate refusal for absence, invalid numbers and range errors while retaining numeric strings and genuine zero.
 * @returns {void}
 */
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
  assert.deepEqual(MapEngine.coordinatesOf({ lon: 0, lat: 0 }), {
    lon: 0,
    lat: 0,
  });
});

/**
 * Verify construction creates the three public DOM surfaces with focus and live-region attributes.
 * @returns {void}
 */
test("the engine exposes canvas, accessible list and live region", () => {
  const { engine, container } = makeEngine();
  assert.equal(container.children.length, 3);
  assert.equal(engine.canvas.tagName, "canvas");
  assert.equal(engine.canvas.getAttribute("tabindex"), "0");
  const ariaLabel = engine.canvas.getAttribute("aria-label");
  assert.ok(ariaLabel, "canvas accessible label is absent");
  assert.ok(ariaLabel.length > 40);
  assert.equal(engine.srList.tagName, "ul");
  assert.equal(engine.status.getAttribute("aria-live"), "polite");
});

/**
 * Verify the shipped dataset retains focusable accessible entries and a keyboard-focusable canvas.
 * @returns {void}
 */
test("the keyboard path never disappears as the dataset grows", () => {
  // The previous SVG map set tabindex to -1 above 500 rows, silently removing
  // keyboard access exactly when the dataset was complete. Assert the
  // opposite: focusable entries exist at full dataset size.
  const { engine } = makeEngine();
  engine.setData(realRows());
  assert.ok(engine.points.length > 12000, "expected the full dataset");
  const buttons = Array.from(engine.srList.children).filter(
    /**
     * Select list items containing an actual button-shaped child.
     * @param {import("../engine.js").EngineElement} li Accessible list item.
     * @returns {boolean} Whether the item contains a button.
     */
    (li) =>
      Array.from(li.children).some(
        /**
         * Identify the existing adapter's button tag.
         * @param {import("../engine.js").EngineElement} c Child element.
         * @returns {boolean} Whether it is a button.
         */
        (c) => c.tagName === "button",
      ),
  );
  assert.ok(buttons.length > 0, "no focusable records exposed");
  assert.equal(
    engine.canvas.getAttribute("tabindex"),
    "0",
    "canvas lost keyboard focus",
  );
});

/**
 * Verify the capped list explicitly announces its remaining original records.
 * @returns {void}
 */
test("the accessible list says how many records it could not list", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  const last = engine.srList.children[engine.srList.children.length - 1];
  assert.ok(
    typeof last.textContent === "string",
    "remaining-count note has no text",
  );
  assert.match(last.textContent, /A further \d+ records match/);
});

/**
 * Verify reprojected count and mapped status conserve the shipped rows accepted by the coordinate parser.
 * @returns {void}
 */
test("projecting the real dataset keeps every mappable record", () => {
  const rows = realRows();
  const { engine } = makeEngine();
  engine.setData(rows);
  const expected = rows.filter(
    /**
     * Count original source rows accepted by the public coordinate parser.
     * @param {import("../engine.js").FacilityRow} r Original shipped row.
     * @returns {boolean} Whether usable coordinates exist.
     */
    (r) => MapEngine.coordinatesOf(r) !== null,
  ).length;
  assert.equal(engine.points.length, expected);
  assert.equal(engine.mapped, expected);
  assert.ok(expected > 12000, `only ${expected} records were mappable`);
});

/**
 * Verify changing to plate carrée preserves record count while actually changing projected geometry.
 * @returns {void}
 */
test("switching projection re-projects without losing records", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  const before = engine.points.length;
  const firstX = engine.points[0].x;
  engine.setProjection("plate-carree");
  assert.equal(engine.points.length, before, "records lost on reprojection");
  assert.notEqual(
    engine.points[0].x,
    firstX,
    "coordinates did not actually change",
  );
  assert.equal(engine.projection.id, "plate-carree");
});

/**
 * Verify projection lookup refuses an unregistered identifier through the actual engine method.
 * @returns {void}
 */
test("an unknown projection is rejected rather than silently ignored", () => {
  const { engine } = makeEngine();
  assert.throws(
    /**
     * Request the unregistered projection through the public method.
     * @returns {void}
     */
    () => engine.setProjection("mercator"),
    /unknown projection/,
  );
});

/**
 * Verify spatial lookup returns the original target row at its centred screen position.
 * @returns {void}
 */
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

/**
 * Verify a distant screen position refuses selection in an actual one-record spatial index.
 * @returns {void}
 */
test("hit testing empty space returns nothing", () => {
  const { engine } = makeEngine();
  engine.setData([{ lon: 0, lat: 0, name: "origin", domain: "fission" }]);
  engine.viewport.resize(960, 480);
  assert.equal(engine.pointAt(-500, -500), null);
});

/**
 * Verify the selection callback receives the identical source object rather than a reconstructed copy.
 * @returns {void}
 */
test("selection is emitted with the original source row", () => {
  /** @type {import("../engine.js").FacilityRow|null} */
  let received = null;
  const { engine } = makeEngine({
    onSelect:
      /**
       * Retain the emitted source object for an independent identity assertion.
       * @param {import("../engine.js").FacilityRow} row Original selected row.
       * @returns {void}
       */
      (row) => {
        received = row;
      },
  });
  const row = {
    lon: 10,
    lat: 20,
    name: "Test site",
    domain: "fusion",
    id: "x1",
  };
  engine.setData([row]);
  engine.emitSelection(engine.points[0]);
  assert.equal(
    received,
    row,
    "the caller must receive the untouched source row",
  );
});

/**
 * Verify handled keys change viewport state and cancel native page scrolling.
 * @returns {void}
 */
test("keyboard panning, zooming and reset all respond", () => {
  const { engine } = makeEngine();
  engine.setData(realRows());
  engine.viewport.resize(960, 480);
  engine.viewport.zoom = 8;
  engine.viewport.clampCentre();
  /** @type {string[]} */
  const prevented = [];
  /**
   * Send one public key command and record default-scroll cancellation.
   * @param {string} key Actual keyboard command.
   * @returns {void}
   */
  const press = (key) => {
    engine.handleKey({
      key,
      shiftKey: false,
      preventDefault:
        /**
         * Retain which handled key cancelled scrolling.
         * @returns {number} Updated observation count.
         */
        () => prevented.push(key),
    });
  };
  const startX = engine.viewport.centreX;
  press("ArrowRight");
  assert.notEqual(engine.viewport.centreX, startX, "arrow key did not pan");
  const zoom = engine.viewport.zoom;
  press("+");
  assert.ok(engine.viewport.zoom > zoom, "plus did not zoom in");
  press("-");
  press("0");
  assert.equal(
    engine.viewport.zoom,
    engine.viewport.minZoom,
    "zero did not reset",
  );
  assert.ok(
    prevented.length >= 4,
    "handled keys must prevent default scrolling",
  );
});

/**
 * Verify Tab remains available to native focus navigation without cancelling its default.
 * @returns {void}
 */
test("unhandled keys are left alone for the browser", () => {
  const { engine } = makeEngine();
  let prevented = false;
  engine.handleKey({
    key: "Tab",
    preventDefault:
      /**
       * Observe whether the unhandled key cancels native focus navigation.
       * @returns {void}
       */
      () => {
        prevented = true;
      },
  });
  assert.equal(
    prevented,
    false,
    "Tab must remain available for focus movement",
  );
});

/**
 * Verify hover focus announces the source name and country through the live region.
 * @returns {void}
 */
test("activating a record announces it to assistive technology", () => {
  const { engine } = makeEngine();
  engine.setData([
    {
      lon: 10,
      lat: 20,
      name: "Announced site",
      country: "Nowhere",
      domain: "fusion",
    },
  ]);
  engine.viewport.resize(960, 480);
  const screen = engine.viewport.toScreen(
    engine.points[0].x,
    engine.points[0].y,
  );
  engine.setFocusFromScreen(screen.x, screen.y);
  assert.ok(
    typeof engine.status.textContent === "string",
    "live region has no text",
  );
  assert.match(engine.status.textContent, /Announced site/);
  assert.match(engine.status.textContent, /Nowhere/);
});

/**
 * Verify missing source text uses explicit display fallback without modifying the source row.
 * @returns {void}
 */
test("a record with no name or country still announces something useful", () => {
  const { engine } = makeEngine();
  engine.setData([{ lon: 10, lat: 20, domain: "fusion" }]);
  engine.viewport.resize(960, 480);
  const screen = engine.viewport.toScreen(
    engine.points[0].x,
    engine.points[0].y,
  );
  engine.setFocusFromScreen(screen.x, screen.y);
  assert.ok(
    typeof engine.status.textContent === "string",
    "live region has no text",
  );
  assert.match(engine.status.textContent, /Unnamed record/);
  assert.match(engine.status.textContent, /location not supplied/);
});

/**
 * Verify the empty-data boundary leaves no indexed points, hit or accessible entries.
 * @returns {void}
 */
test("an empty dataset leaves the engine usable", () => {
  const { engine } = makeEngine();
  engine.setData([]);
  assert.equal(engine.points.length, 0);
  assert.equal(engine.pointAt(10, 10), null);
  assert.equal(engine.srList.children.length, 0);
});

/**
 * JSON-like nonnumeric coordinates cannot manufacture geographic zero or one.
 * @returns {void}
 */
test("nonnumeric and blank coordinates remain unusable", () => {
  for (const row of [
    { lon: false, lat: 0 },
    { lon: 0, lat: true },
    { lon: [], lat: 0 },
    { lon: {}, lat: 0 },
    { lon: "   ", lat: 0 },
    { lon: 0, lat: "\t" },
  ]) {
    assert.equal(MapEngine.coordinatesOf(row), null, JSON.stringify(row));
  }
  assert.deepEqual(MapEngine.coordinatesOf({ lon: " 12.5 ", lat: " -3.25 " }), {
    lon: 12.5,
    lat: -3.25,
  });
  assert.deepEqual(MapEngine.coordinatesOf({ lon: -180, lat: -90 }), {
    lon: -180,
    lat: -90,
  });
  assert.deepEqual(MapEngine.coordinatesOf({ lon: 180, lat: 90 }), {
    lon: 180,
    lat: 90,
  });
});

/**
 * Reprojection rebinds focus to the new indexed point, and filtering cannot select a removed row.
 * @returns {void}
 */
test("reprojection refreshes focus and removed rows cannot remain selected", () => {
  /** @type {import("../engine.js").FacilityRow[]} */
  const selections = [];
  const { engine } = makeEngine({
    /**
     * Observe every original row actually emitted by the public selection path.
     * @param {import("../engine.js").FacilityRow} row Selected source object.
     * @returns {void}
     */
    onSelect: (row) => {
      selections.push(row);
    },
  });
  const row = realRows().find(
    /**
     * Select one unchanged mappable source row from the shipped document.
     * @param {import("../engine.js").FacilityRow} candidate Original record.
     * @returns {boolean} Whether the actual coordinate parser accepts it.
     */
    (candidate) => MapEngine.coordinatesOf(candidate) !== null,
  );
  assert.ok(row, "no shipped mappable row");
  engine.setData([row]);
  engine.focusPoint(engine.points[0]);
  const oldPoint = engine.focus;
  engine.setProjection("plate-carree");
  assert.equal(
    engine.focus,
    engine.points[0],
    "focus did not rebind to the current spatial index",
  );
  assert.notEqual(
    engine.focus,
    oldPoint,
    "old projected point survived reprojection",
  );
  assert.equal(engine.focus.row, row, "source object identity changed");
  engine.setData([]);
  assert.equal(engine.focus, null, "filtered row remains focused");
  engine.handleKey({
    key: "Enter",
    /**
     * Accept the handled activation key without changing the recorded selections.
     * @returns {void}
     */
    preventDefault: () => {},
  });
  assert.deepEqual(
    selections,
    [],
    "activation emitted a row absent from the dataset",
  );
});

/**
 * Refuse every missing host form before creating or mounting map components.
 * @returns {void}
 */
test("missing host and owner document refuse before mounting", () => {
  assert.throws(
    /**
     * Invoke construction without an options object.
     * @returns {InstanceType<typeof MapEngine>} Instance only if the required refusal is broken.
     */
    () => new MapEngine(),
    /container element is required/,
  );
  assert.throws(
    /**
     * Invoke construction with explicitly absent options.
     * @returns {InstanceType<typeof MapEngine>} Instance only if the required refusal is broken.
     */
    () => new MapEngine(null),
    /container element is required/,
  );
  const container = makeElement("div");
  assert.throws(
    /**
     * Supply an unattached host without a document override.
     * @returns {InstanceType<typeof MapEngine>} Instance only if the required refusal is broken.
     */
    () => new MapEngine({ container }),
    /a document is required/,
  );
  assert.equal(container.children.length, 0, "invalid host was partly mounted");
});

/**
 * Construction honours the explicit document and build returns its actual mounted components.
 * @returns {void}
 */
test("explicit document and build expose the mounted component identities", () => {
  const document = makeDocument();
  const { engine, container } = makeEngine({ document });
  assert.equal(engine.document, document);
  assert.notEqual(container.ownerDocument, document);
  assert.equal(engine.canvas.ownerDocument, document);
  const components = engine.build();
  assert.equal(components.canvas, engine.canvas);
  assert.equal(components.srList, engine.srList);
  assert.equal(components.status, engine.status);
  assert.equal(container.children.length, 6);
  assert.equal(container.children[3], components.canvas);
  assert.equal(container.children[4], components.srList);
  assert.equal(container.children[5], components.status);
});

/**
 * Load the actual classic script with each native namespace-host convention and construct a working map.
 * @returns {void}
 */
test("classic scripts publish the same API on self and the global host", () => {
  const code = fs.readFileSync(path.join(__dirname, "..", "engine.js"), "utf8");
  for (const useSelf of [true, false]) {
    /** @type {import("../engine.js").EngineGlobal} */
    const host = {
      AtlasMap: {
        projection: require("../projection.js"),
        coastline: require("../coastline.js"),
        Quadtree: require("../quadtree.js"),
        cluster: require("../cluster.js"),
        Viewport: require("../viewport.js"),
        renderer: require("../renderer.js"),
        interactions: require("../interactions.js"),
        accessibility: require("../accessibility.js"),
      },
    };
    vm.runInNewContext(code, useSelf ? { self: host } : host, {
      filename: path.join(__dirname, "..", "engine.js"),
    });
    const Engine = host.AtlasMap && host.AtlasMap.MapEngine;
    assert.ok(Engine, "classic constructor was not published");
    const document = makeDocument();
    const container = document.createElement("div");
    const engine = new Engine({ container });
    assert.equal(engine.document, document, "owner document was not used");
    engine.setData(realRows());
    assert.equal(engine.points.length, 13357);
    assert.equal(engine.points[0].row, engine.rows[0]);
    assert.equal(Engine.KEYBOARD_LIST_LIMIT, MapEngine.KEYBOARD_LIST_LIMIT);
    assert.deepEqual(
      JSON.parse(JSON.stringify(Engine.coordinatesOf({ lon: 0, lat: 0 }))),
      {
        lon: 0,
        lat: 0,
      },
    );
  }
});

/**
 * Every omitted classic dependency refuses before publishing a constructor.
 * @returns {void}
 */
test("classic loading refuses absent namespace and each missing map module", () => {
  const code = fs.readFileSync(path.join(__dirname, "..", "engine.js"), "utf8");
  assert.throws(
    /**
     * Load the shipped classic script before its map namespace exists.
     * @returns {unknown} Native VM result only if the required refusal is broken.
     */
    () =>
      vm.runInNewContext(
        code,
        {},
        { filename: path.join(__dirname, "..", "engine.js") },
      ),
    /load all map modules before engine.js/,
  );
  /** @type {Partial<import("../engine.js").EngineNamespace>} */
  const modules = {
    projection: require("../projection.js"),
    coastline: require("../coastline.js"),
    Quadtree: require("../quadtree.js"),
    cluster: require("../cluster.js"),
    Viewport: require("../viewport.js"),
    renderer: require("../renderer.js"),
    interactions: require("../interactions.js"),
    accessibility: require("../accessibility.js"),
  };
  /** @type {(keyof typeof modules)[]} */
  const dependencies = [
    "projection",
    "coastline",
    "Quadtree",
    "cluster",
    "Viewport",
    "renderer",
    "interactions",
    "accessibility",
  ];
  for (const dependency of dependencies) {
    const host = { AtlasMap: { ...modules } };
    delete host.AtlasMap[dependency];
    assert.throws(
      /**
       * Load the shipped constructor with one of its actual dependencies absent.
       * @returns {unknown} Native VM result only if the required refusal is broken.
       */
      () =>
        vm.runInNewContext(
          code,
          { self: host },
          { filename: path.join(__dirname, "..", "engine.js") },
        ),
      /load all map modules before engine.js/,
      dependency,
    );
    assert.equal(
      host.AtlasMap.MapEngine,
      undefined,
      "refused constructor was published",
    );
  }
});
