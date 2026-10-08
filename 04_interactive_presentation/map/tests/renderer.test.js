// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — renderer tests against a recording canvas context.

"use strict";

const test = require("node:test");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const renderer = require("../renderer.js");
const cluster = require("../cluster.js");
const Viewport = require("../viewport.js");
const projection = require("../projection.js");

/**
 * One observed canvas method call or state assignment, retaining its supplied arguments.
 * @typedef {{name: string, args: unknown[], fillStyle?: unknown, alpha?: unknown}} CanvasCall
 */

/**
 * Recording adapter exposing exactly the renderer's canvas boundary and observed calls.
 * @typedef {import("../renderer.js").DrawingContext & {calls: CanvasCall[]}} RecordingContext
 */

const WORLD = projection.bounds(projection.equalEarth, 5);

/**
 * A canvas 2D context that records the calls made against it.
 *
 * Painting cannot be asserted pixel-by-pixel in a headless test, but the
 * sequence of drawing calls is the thing that actually carries the bugs:
 * wrong ordering, missing save/restore, unbalanced state.
 * @returns {RecordingContext} Proxy-backed call recorder; this does not rasterise pixels.
 */
function recordingContext() {
  /** @type {CanvasCall[]} */
  const calls = [];
  /** @type {Record<string|symbol, unknown>} */
  const state = {
    fillStyle: null,
    strokeStyle: null,
    globalAlpha: 1,
    font: null,
  };
  const handler = {
    /**
     * Return recorded state or a method recorder for a string property.
     * @param {object} target Unused proxy target.
     * @param {string|symbol} prop Requested property.
     * @returns {unknown} Recorded state, a recording function, or undefined for unknown symbols.
     */
    get(target, prop) {
      if (prop === "calls") return calls;
      if (prop in state) return state[prop];
      if (typeof prop === "string") {
        return (
          /**
           * Retain one invoked method's arguments and current fill/alpha state.
           * @param {...unknown} args Actual arguments supplied to the context method.
           * @returns {void}
           */
          (...args) => {
            calls.push({
              name: prop,
              args,
              fillStyle: state.fillStyle,
              alpha: state.globalAlpha,
            });
          }
        );
      }
      return undefined;
    },
    /**
     * Record a state assignment before accepting it on the adapter.
     * @param {object} target Unused proxy target.
     * @param {string|symbol} prop Assigned property.
     * @param {unknown} value Actual assigned value.
     * @returns {boolean} True so the Proxy assignment succeeds.
     */
    set(target, prop, value) {
      state[prop] = value;
      calls.push({ name: "set:" + String(prop), args: [value] });
      return true;
    },
  };
  return /** @type {RecordingContext} */ (
    /** @type {unknown} */ (new Proxy({}, handler))
  );
}

/**
 * Names of the calls recorded, in order.
 * @param {RecordingContext} ctx A recording context.
 * @returns {Array<string>} Call names.
 */
function names(ctx) {
  return ctx.calls.map(
    /**
     * Extract one observed call or assignment name.
     * @param {CanvasCall} c Recorded observation.
     * @returns {string} Method or assignment name.
     */
    (c) => c.name,
  );
}

/**
 * Verify the ocean fill covers the supplied canvas dimensions with the configured colour.
 * @returns {void}
 */
test("background fills the whole canvas in the ocean colour", () => {
  const ctx = recordingContext();
  renderer.drawBackground(ctx, { width: 800, height: 400 });
  const fill = ctx.calls.find(
    /**
     * Locate the first observed fillRect canvas call.
     * @param {CanvasCall} c Recorded observation.
     * @returns {boolean} Whether this call is fillRect.
     */
    (c) => c.name === "fillRect",
  );
  assert.ok(fill, "no fillRect issued");
  assert.deepEqual(fill.args, [0, 0, 800, 400]);
  assert.equal(fill.fillStyle, renderer.THEME.ocean);
});

/**
 * Verify every public painter restores the state it saves on the recording context.
 * @returns {void}
 */
test("every draw call balances save and restore", () => {
  // An unbalanced context leaks fill styles into later drawing, which shows up
  // as sporadic mis-coloured frames that are painful to reproduce by hand.
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const proj = projection.equalEarth;
  const cases = [
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) => renderer.drawBackground(ctx, viewport),
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) => renderer.drawGraticule(ctx, viewport, proj),
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) =>
      renderer.drawLand(ctx, viewport, proj, [
        [
          [0, 0],
          [10, 0],
          [10, 10],
        ],
      ]),
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) =>
      renderer.drawClusters(
        ctx,
        [{ x: 1, y: 2, count: 3, domain: "fission" }],
        { radiusFor: cluster.radiusFor },
      ),
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) =>
      renderer.drawClusterLabels(
        ctx,
        [{ x: 1, y: 2, count: 40, domain: "fission" }],
        cluster.radiusFor,
      ),
    /**
     * Invoke this public painter on a fresh recording context.
     * @param {RecordingContext} ctx Call-recording context.
     * @returns {void}
     */
    (ctx) =>
      renderer.drawFocus(ctx, { x: 1, y: 2, count: 1 }, cluster.radiusFor),
  ];
  for (const run of cases) {
    const ctx = recordingContext();
    run(ctx);
    const list = names(ctx);
    assert.equal(
      list.filter(
        /**
         * Count observed save calls.
         * @param {string} n Observed method or assignment name.
         * @returns {boolean} Whether the name matches.
         */
        (n) => n === "save",
      ).length,
      list.filter(
        /**
         * Count observed restore calls.
         * @param {string} n Observed method or assignment name.
         * @returns {boolean} Whether the name matches.
         */
        (n) => n === "restore",
      ).length,
      `unbalanced save/restore in ${run.toString().slice(0, 60)}`,
    );
  }
});

/**
 * Verify mixed input order paints chemical before fission before fusion glyphs.
 * @returns {void}
 */
test("rare domains are painted last so they cannot be buried", () => {
  // This is the ordering that keeps 159 fusion devices visible against
  // 10,665 chemical sites.
  const ctx = recordingContext();
  const clusters = [
    { x: 1, y: 1, count: 5, domain: "fusion" },
    { x: 2, y: 2, count: 5, domain: "chemical" },
    { x: 3, y: 3, count: 5, domain: "fission" },
  ];
  renderer.drawClusters(ctx, clusters, { radiusFor: cluster.radiusFor });
  const painted = ctx.calls
    .filter(
      /**
       * Select arc observations from the painter's call stream.
       * @param {CanvasCall} c Recorded observation.
       * @returns {boolean} Whether the method matches.
       */
      (c) => c.name === "arc",
    )
    .map(
      /**
       * Retain each arc's screen x to compare paint order.
       * @param {CanvasCall} c Recorded arc.
       * @returns {unknown} First method argument.
       */
      (c) => c.args[0],
    );
  assert.deepEqual(
    painted,
    [2, 3, 1],
    "chemical, then fission, then fusion expected",
  );
});

/**
 * Verify sorting for paint order leaves the caller-owned array and its entries unchanged.
 * @returns {void}
 */
test("drawClusters does not mutate the caller's array", () => {
  const clusters = [
    { x: 1, y: 1, count: 1, domain: "fusion" },
    { x: 2, y: 2, count: 1, domain: "chemical" },
  ];
  const before = clusters.slice();
  renderer.drawClusters(recordingContext(), clusters, {
    radiusFor: cluster.radiusFor,
  });
  assert.deepEqual(
    clusters,
    before,
    "cluster ordering leaked back to the caller",
  );
});

/**
 * Verify the land painter requests the even-odd fill rule from its real canvas boundary.
 * @returns {void}
 */
test("land is filled with the even-odd rule so lakes stay cut out", () => {
  const ctx = recordingContext();
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  renderer.drawLand(ctx, viewport, projection.equalEarth, [
    [
      [0, 0],
      [10, 0],
      [10, 10],
    ],
  ]);
  const fill = ctx.calls.find(
    /**
     * Locate the first observed fill canvas call.
     * @param {CanvasCall} c Recorded observation.
     * @returns {boolean} Whether this call is fill.
     */
    (c) => c.name === "fill",
  );
  assert.ok(fill, "land was never filled");
  assert.deepEqual(fill.args, ["evenodd"]);
});

/**
 * Verify every supplied geographic ring starts and closes its own canvas subpath.
 * @returns {void}
 */
test("land rings are closed, so coastlines do not leak fill", () => {
  const ctx = recordingContext();
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  /** @type {[number, number][][]} */
  const rings = [
    [
      [0, 0],
      [10, 0],
      [10, 10],
    ],
    [
      [20, 20],
      [30, 20],
      [30, 30],
    ],
  ];
  renderer.drawLand(ctx, viewport, projection.equalEarth, rings);
  assert.equal(
    names(ctx).filter(
      /**
       * Count observed closePath calls.
       * @param {string} n Observed method or assignment name.
       * @returns {boolean} Whether the name matches.
       */
      (n) => n === "closePath",
    ).length,
    rings.length,
  );
  assert.equal(
    names(ctx).filter(
      /**
       * Count observed moveTo calls.
       * @param {string} n Observed method or assignment name.
       * @returns {boolean} Whether the name matches.
       */
      (n) => n === "moveTo",
    ).length,
    rings.length,
  );
});

/**
 * Verify singleton and small-radius clusters are omitted while a readable cluster gets its count.
 * @returns {void}
 */
test("only clusters large enough to read are labelled", () => {
  const ctx = recordingContext();
  renderer.drawClusterLabels(
    ctx,
    [
      { x: 1, y: 1, count: 1, domain: "fission" },
      { x: 2, y: 2, count: 2, domain: "fission" },
      { x: 3, y: 3, count: 400, domain: "fission" },
    ],
    cluster.radiusFor,
  );
  const labels = ctx.calls.filter(
    /**
     * Select fillText observations from the painter's call stream.
     * @param {CanvasCall} c Recorded observation.
     * @returns {boolean} Whether the method matches.
     */
    (c) => c.name === "fillText",
  );
  assert.equal(
    labels.length,
    1,
    "expected only the large cluster to be labelled",
  );
  assert.equal(labels[0].args[0], "400");
});

/**
 * Verify count labels at the thousand boundary and a representative rounded abbreviation.
 * @returns {void}
 */
test("counts abbreviate above a thousand", () => {
  assert.equal(renderer.formatCount(7), "7");
  assert.equal(renderer.formatCount(999), "999");
  assert.equal(renderer.formatCount(1000), "1k");
  assert.equal(renderer.formatCount(12813), "12.8k");
});

/**
 * Verify the four known domains return CSS hex colours and absent or unknown domains fall back.
 * @returns {void}
 */
test("domain colours are defined for every domain in the real dataset", () => {
  for (const domain of ["fission", "fusion", "chemical", "hybrid"]) {
    assert.match(renderer.domainColour(domain), /^#[0-9a-f]{6}$/i, domain);
  }
  assert.equal(
    renderer.domainColour("nonsense"),
    renderer.THEME.domains.unknown,
  );
  assert.equal(
    renderer.domainColour(undefined),
    renderer.THEME.domains.unknown,
  );
});

/**
 * Verify absent focus paints nothing and an active glyph receives a larger surrounding ring.
 * @returns {void}
 */
test("focus ring is drawn outside the glyph and skipped when nothing is active", () => {
  const ctx = recordingContext();
  renderer.drawFocus(ctx, null, cluster.radiusFor);
  assert.equal(ctx.calls.length, 0, "drew a focus ring for nothing");
  const ctx2 = recordingContext();
  renderer.drawFocus(ctx2, { x: 5, y: 6, count: 1 }, cluster.radiusFor);
  const arc = ctx2.calls.find(
    /**
     * Locate the first observed arc canvas call.
     * @param {CanvasCall} c Recorded observation.
     * @returns {boolean} Whether this call is arc.
     */
    (c) => c.name === "arc",
  );
  assert.ok(arc, "no focus arc issued");
  assert.ok(typeof arc.args[2] === "number", "focus radius is not numeric");
  assert.ok(
    arc.args[2] > cluster.radiusFor(1),
    "focus ring not outside the glyph",
  );
});

/**
 * Verify the public painting sequence never assigns a canvas shadow property.
 * @returns {void}
 */
test("no drop shadow is ever set — the defect the engine replaces", () => {
  // The previous SVG map applied a per-point drop shadow, which is what turned
  // dense regions into unreadable black mass. Guard against reintroducing it.
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const ctx = recordingContext();
  renderer.drawBackground(ctx, viewport);
  renderer.drawGraticule(ctx, viewport, projection.equalEarth);
  renderer.drawLand(ctx, viewport, projection.equalEarth, [
    [
      [0, 0],
      [10, 0],
      [10, 10],
    ],
  ]);
  renderer.drawClusters(ctx, [{ x: 1, y: 1, count: 9, domain: "chemical" }], {
    radiusFor: cluster.radiusFor,
  });
  const shadowed = names(ctx).filter(
    /**
     * Detect any method or state assignment mentioning a shadow.
     * @param {string} n Observed name.
     * @returns {boolean} Whether a shadow was touched.
     */
    (n) => n.indexOf("shadow") !== -1,
  );
  assert.deepEqual(shadowed, [], `shadow properties were set: ${shadowed}`);
});

/**
 * Unregistered names, including Object prototype keys, always resolve to a CSS colour.
 * @returns {void}
 */
test("prototype names cannot replace the unknown domain colour", () => {
  for (const domain of [
    "toString",
    "constructor",
    "valueOf",
    "__proto__",
    "",
    null,
  ]) {
    assert.equal(renderer.domainColour(domain), renderer.THEME.domains.unknown);
  }
});

/**
 * Refuse graticule steps that hang the real loops or are not numeric spacing.
 * @returns {void}
 */
test("invalid graticule spacing refuses before touching canvas state", () => {
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  for (const step of [
    -30,
    -Infinity,
    Infinity,
    NaN,
    Number.MIN_VALUE,
    "30",
    false,
    {},
  ]) {
    const ctx = recordingContext();
    assert.throws(
      /**
       * Invoke the real API reflectively to exercise deliberately invalid runtime inputs.
       * @returns {void}
       */
      () =>
        Reflect.apply(renderer.drawGraticule, undefined, [
          ctx,
          viewport,
          projection.equalEarth,
          step,
        ]),
      {
        name: "RangeError",
        message:
          "Graticule spacing must be finite, positive and advance longitude.",
      },
    );
    assert.deepEqual(ctx.calls, [], "invalid spacing changed canvas state");
  }
});

/**
 * Existing omitted, zero and null spacing contracts render exactly the default grid.
 * @returns {void}
 */
test("default graticule spacing is preserved for omitted zero and null", () => {
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const reference = recordingContext();
  renderer.drawGraticule(reference, viewport, projection.equalEarth, 30);
  for (const step of [undefined, 0, null]) {
    const ctx = recordingContext();
    renderer.drawGraticule(ctx, viewport, projection.equalEarth, step);
    assert.deepEqual(ctx.calls, reference.calls);
  }
});

/**
 * The actual classic script publishes the same painters with and without a self host.
 * @returns {void}
 */
test("classic-script hosts expose the same palette and painter contracts", () => {
  const filename = path.join(__dirname, "../renderer.js");
  const source = fs.readFileSync(filename, "utf8");
  /** @type {(import("../renderer.js").RendererGlobal & {self?: import("../renderer.js").RendererGlobal})[]} */
  const hosts = [{}, { self: {} }];
  for (const host of hosts) {
    vm.runInNewContext(source, host, { filename });
    const namespace = (host.self || host).AtlasMap;
    assert.ok(
      namespace && namespace.renderer,
      "classic script did not publish its API",
    );
    const api = namespace.renderer;
    assert.equal(api.domainColour("fusion"), renderer.THEME.domains.fusion);
    assert.equal(
      api.domainColour("constructor"),
      renderer.THEME.domains.unknown,
    );
    const ctx = recordingContext();
    api.drawBackground(ctx, { width: 40, height: 20 });
    assert.deepEqual(names(ctx), [
      "save",
      "set:fillStyle",
      "fillRect",
      "restore",
    ]);
    assert.deepEqual(ctx.calls[2].args, [0, 0, 40, 20]);
  }
});

/**
 * An accented cluster paints according to the supplied order and strokes its minority colour.
 * @returns {void}
 */
test("custom paint order uses minority accents and colours their rings", () => {
  const ctx = recordingContext();
  const entries = [
    { x: 1, y: 1, count: 400, domain: "chemical", accent: "fusion" },
    { x: 2, y: 2, count: 1, domain: "fission" },
    { x: 3, y: 3, count: 1, domain: "unregistered" },
  ];
  renderer.drawClusters(ctx, entries, {
    radiusFor: cluster.radiusFor,
    order: ["fusion", "fission"],
  });
  const arcs = ctx.calls.filter(
    /**
     * Select the glyph calls whose screen x encodes the known input identity.
     * @param {CanvasCall} call Recorded canvas observation.
     * @returns {boolean} Whether the method paints an arc.
     */
    (call) => call.name === "arc",
  );
  assert.deepEqual(
    arcs.map(
      /**
       * Extract each glyph's screen x for an independent order assertion.
       * @param {CanvasCall} call Recorded arc.
       * @returns {unknown} First actual arc argument.
       */
      (call) => call.args[0],
    ),
    [3, 1, 2],
  );
  const ringColour = ctx.calls.find(
    /**
     * Locate the first explicit ring-colour state assignment.
     * @param {CanvasCall} call Recorded observation.
     * @returns {boolean} Whether this is a stroke-style assignment.
     */
    (call) => call.name === "set:strokeStyle",
  );
  assert.ok(ringColour, "no minority ring colour assigned");
  assert.deepEqual(ringColour.args, [renderer.THEME.domains.fusion]);
  const strokes = ctx.calls.filter(
    /**
     * Count actual outlines without conflating them with state assignments.
     * @param {CanvasCall} call Recorded observation.
     * @returns {boolean} Whether this is a stroke call.
     */
    (call) => call.name === "stroke",
  );
  assert.equal(
    strokes.length,
    1,
    "singleton glyphs received an unwanted outline",
  );
});

/**
 * An empty cluster list preserves balanced state even without required sizing options.
 * @returns {void}
 */
test("empty cluster lists retain the existing no-options behaviour", () => {
  const ctx = recordingContext();
  Reflect.apply(renderer.drawClusters, undefined, [ctx, [], null]);
  assert.deepEqual(names(ctx), ["save", "restore"]);
});
