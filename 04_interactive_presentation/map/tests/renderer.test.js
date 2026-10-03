// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — renderer tests against a recording canvas context.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const renderer = require("../renderer.js");
const cluster = require("../cluster.js");
const Viewport = require("../viewport.js");
const projection = require("../projection.js");

const WORLD = projection.bounds(projection.equalEarth, 5);

/**
 * A canvas 2D context that records the calls made against it.
 *
 * Painting cannot be asserted pixel-by-pixel in a headless test, but the
 * sequence of drawing calls is the thing that actually carries the bugs:
 * wrong ordering, missing save/restore, unbalanced state.
 *
 * @returns {object} A recording context.
 */
function recordingContext() {
  const calls = [];
  const state = { fillStyle: null, strokeStyle: null, globalAlpha: 1, font: null };
  const handler = {
    get(target, prop) {
      if (prop === "calls") return calls;
      if (prop in state) return state[prop];
      if (typeof prop === "string") {
        return (...args) => {
          calls.push({ name: prop, args, fillStyle: state.fillStyle, alpha: state.globalAlpha });
        };
      }
      return undefined;
    },
    set(target, prop, value) {
      state[prop] = value;
      calls.push({ name: "set:" + String(prop), args: [value] });
      return true;
    },
  };
  return new Proxy({}, handler);
}

/**
 * Names of the calls recorded, in order.
 *
 * @param {object} ctx A recording context.
 * @returns {Array<string>} Call names.
 */
function names(ctx) {
  return ctx.calls.map((c) => c.name);
}

test("background fills the whole canvas in the ocean colour", () => {
  const ctx = recordingContext();
  renderer.drawBackground(ctx, { width: 800, height: 400 });
  const fill = ctx.calls.find((c) => c.name === "fillRect");
  assert.ok(fill, "no fillRect issued");
  assert.deepEqual(fill.args, [0, 0, 800, 400]);
  assert.equal(fill.fillStyle, renderer.THEME.ocean);
});

test("every draw call balances save and restore", () => {
  // An unbalanced context leaks fill styles into later drawing, which shows up
  // as sporadic mis-coloured frames that are painful to reproduce by hand.
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const proj = projection.equalEarth;
  const cases = [
    (ctx) => renderer.drawBackground(ctx, viewport),
    (ctx) => renderer.drawGraticule(ctx, viewport, proj),
    (ctx) => renderer.drawLand(ctx, viewport, proj, [[[0, 0], [10, 0], [10, 10]]]),
    (ctx) => renderer.drawClusters(ctx, [{ x: 1, y: 2, count: 3, domain: "fission" }], { radiusFor: cluster.radiusFor }),
    (ctx) => renderer.drawClusterLabels(ctx, [{ x: 1, y: 2, count: 40, domain: "fission" }], cluster.radiusFor),
    (ctx) => renderer.drawFocus(ctx, { x: 1, y: 2, count: 1 }, cluster.radiusFor),
  ];
  for (const run of cases) {
    const ctx = recordingContext();
    run(ctx);
    const list = names(ctx);
    assert.equal(
      list.filter((n) => n === "save").length,
      list.filter((n) => n === "restore").length,
      `unbalanced save/restore in ${run.toString().slice(0, 60)}`,
    );
  }
});

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
    .filter((c) => c.name === "arc")
    .map((c) => c.args[0]);
  assert.deepEqual(painted, [2, 3, 1], "chemical, then fission, then fusion expected");
});

test("drawClusters does not mutate the caller's array", () => {
  const clusters = [
    { x: 1, y: 1, count: 1, domain: "fusion" },
    { x: 2, y: 2, count: 1, domain: "chemical" },
  ];
  const before = clusters.slice();
  renderer.drawClusters(recordingContext(), clusters, { radiusFor: cluster.radiusFor });
  assert.deepEqual(clusters, before, "cluster ordering leaked back to the caller");
});

test("land is filled with the even-odd rule so lakes stay cut out", () => {
  const ctx = recordingContext();
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  renderer.drawLand(ctx, viewport, projection.equalEarth, [[[0, 0], [10, 0], [10, 10]]]);
  const fill = ctx.calls.find((c) => c.name === "fill");
  assert.ok(fill, "land was never filled");
  assert.deepEqual(fill.args, ["evenodd"]);
});

test("land rings are closed, so coastlines do not leak fill", () => {
  const ctx = recordingContext();
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const rings = [[[0, 0], [10, 0], [10, 10]], [[20, 20], [30, 20], [30, 30]]];
  renderer.drawLand(ctx, viewport, projection.equalEarth, rings);
  assert.equal(names(ctx).filter((n) => n === "closePath").length, rings.length);
  assert.equal(names(ctx).filter((n) => n === "moveTo").length, rings.length);
});

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
  const labels = ctx.calls.filter((c) => c.name === "fillText");
  assert.equal(labels.length, 1, "expected only the large cluster to be labelled");
  assert.equal(labels[0].args[0], "400");
});

test("counts abbreviate above a thousand", () => {
  assert.equal(renderer.formatCount(7), "7");
  assert.equal(renderer.formatCount(999), "999");
  assert.equal(renderer.formatCount(1000), "1k");
  assert.equal(renderer.formatCount(12813), "12.8k");
});

test("domain colours are defined for every domain in the real dataset", () => {
  for (const domain of ["fission", "fusion", "chemical", "hybrid"]) {
    assert.match(renderer.domainColour(domain), /^#[0-9a-f]{6}$/i, domain);
  }
  assert.equal(renderer.domainColour("nonsense"), renderer.THEME.domains.unknown);
  assert.equal(renderer.domainColour(undefined), renderer.THEME.domains.unknown);
});

test("focus ring is drawn outside the glyph and skipped when nothing is active", () => {
  const ctx = recordingContext();
  renderer.drawFocus(ctx, null, cluster.radiusFor);
  assert.equal(ctx.calls.length, 0, "drew a focus ring for nothing");
  const ctx2 = recordingContext();
  renderer.drawFocus(ctx2, { x: 5, y: 6, count: 1 }, cluster.radiusFor);
  const arc = ctx2.calls.find((c) => c.name === "arc");
  assert.ok(arc.args[2] > cluster.radiusFor(1), "focus ring not outside the glyph");
});

test("no drop shadow is ever set — the defect the engine replaces", () => {
  // The previous SVG map applied a per-point drop shadow, which is what turned
  // dense regions into unreadable black mass. Guard against reintroducing it.
  const viewport = new Viewport({ width: 400, height: 200, world: WORLD });
  const ctx = recordingContext();
  renderer.drawBackground(ctx, viewport);
  renderer.drawGraticule(ctx, viewport, projection.equalEarth);
  renderer.drawLand(ctx, viewport, projection.equalEarth, [[[0, 0], [10, 0], [10, 10]]]);
  renderer.drawClusters(ctx, [{ x: 1, y: 1, count: 9, domain: "chemical" }], {
    radiusFor: cluster.radiusFor,
  });
  const shadowed = names(ctx).filter((n) => n.indexOf("shadow") !== -1);
  assert.deepEqual(shadowed, [], `shadow properties were set: ${shadowed}`);
});
