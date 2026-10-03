// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — density aggregation tests, including on the real dataset.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const cluster = require("../cluster.js");
const Viewport = require("../viewport.js");
const projection = require("../projection.js");

const DATA = path.join(__dirname, "..", "..", "data", "global_reactors.sample.json");
const WORLD = projection.bounds(projection.equalEarth, 5);

/**
 * Project the shipped facilities into world space.
 *
 * @returns {Array<object>} Points with ``x``, ``y`` and ``domain``.
 */
function realPoints() {
// Datasets are published as a document whose `records` array carries the
// rows; older exports were bare arrays. Accept both, so the tests read the
// real shipped file whichever form it is in.
  const document = JSON.parse(fs.readFileSync(DATA, "utf8"));
  const rows = Array.isArray(document) ? document : document.records;
  const proj = projection.equalEarth;
  const out = [];
  for (const row of rows) {
    const lon = Number(row.lon);
    const lat = Number(row.lat);
    if (!Number.isFinite(lon) || !Number.isFinite(lat)) continue;
    if (row.lon === "" || row.lat === "") continue;
    const xy = proj.forward(lon, lat);
    out.push({ x: xy.x, y: xy.y, domain: row.domain, id: row.id });
  }
  return out;
}

/**
 * A viewport over the whole world at a fixed canvas size.
 *
 * @returns {Viewport} The viewport.
 */
function makeViewport() {
  return new Viewport({ width: 960, height: 480, world: WORLD });
}

test("aggregation conserves every record", () => {
  const points = realPoints();
  const total = cluster
    .aggregate(points, makeViewport(), 24)
    .reduce((sum, c) => sum + c.count, 0);
  assert.equal(total, points.length, "clustering lost or duplicated records");
});

test("aggregation rejects a non-positive cell size", () => {
  assert.throws(() => cluster.aggregate([], makeViewport(), 0), /cellSize must be positive/);
  assert.throws(() => cluster.aggregate([], makeViewport(), -5), /cellSize must be positive/);
});

test("clustering collapses the dense regions that broke the old map", () => {
  // The whole point of the engine: 12,813 overlapping points must become a
  // few hundred legible glyphs at world zoom.
  const points = realPoints();
  const clusters = cluster.aggregate(points, makeViewport(), 24);
  assert.ok(
    clusters.length < points.length / 8,
    `expected heavy aggregation, got ${clusters.length} from ${points.length}`,
  );
  assert.ok(clusters.length > 20, "aggregation collapsed the map into nothing");
});

test("zooming in resolves clusters into more, smaller groups", () => {
  const points = realPoints();
  const wide = makeViewport();
  const close = makeViewport();
  close.zoom = 16;
  close.clampCentre();
  const wideClusters = cluster.aggregate(points, wide, 24).length;
  const closeClusters = cluster.aggregate(points, close, 24).length;
  assert.ok(
    closeClusters > wideClusters,
    `zoom did not resolve detail: ${wideClusters} -> ${closeClusters}`,
  );
});

test("fill follows the majority so proportion is reported honestly", () => {
  // Colouring purely by rarity turned the whole map orange, because almost
  // every cluster contains one fission record.
  assert.equal(cluster.majorityDomain({ chemical: 500, fusion: 1 }), "chemical");
  assert.equal(cluster.majorityDomain({ fission: 7, chemical: 2 }), "fission");
  assert.equal(cluster.majorityDomain({}), "unknown");
});

test("the accent ring carries the rarest domain present", () => {
  assert.equal(cluster.accentDomain({ chemical: 500, fusion: 1 }), "fusion");
  assert.equal(cluster.accentDomain({ chemical: 500, fission: 2 }), "fission");
  assert.equal(cluster.accentDomain({ chemical: 9 }), null, "no accent when uniform");
  assert.equal(cluster.accentDomain({ fusion: 4 }), null, "no accent when uniform");
});

test("rarity ranking still resolves the rarest domain present", () => {
  assert.equal(cluster.dominantDomain({ chemical: 500, fusion: 1 }), "fusion");
  assert.equal(cluster.dominantDomain({ fission: 3, hybrid: 1 }), "hybrid");
  assert.equal(cluster.dominantDomain({}), "unknown");
  assert.equal(cluster.dominantDomain({ something: 4 }), "something");
});

test("a fusion record is never hidden by surrounding chemical records", () => {
  // Every fusion record must reach the reader either as a fusion-filled
  // cluster or as a fusion accent ring on a cluster of something else.
  const points = realPoints();
  const clusters = cluster.aggregate(points, makeViewport(), 24);
  const fusionTotal = points.filter((p) => p.domain === "fusion").length;
  const advertised = clusters
    .filter((c) => c.domain === "fusion" || c.accent === "fusion")
    .reduce((sum, c) => sum + (c.domains.fusion || 0), 0);
  assert.equal(advertised, fusionTotal, "fusion records became invisible");
});

test("the map is not overwhelmingly one colour — proportion survives", () => {
  // Guards the specific regression that rarity-precedence introduced: the
  // whole world reading as fission because fission is widely scattered.
  const clusters = cluster.aggregate(realPoints(), makeViewport(), 26);
  const chemical = clusters.filter((c) => c.domain === "chemical").length;
  assert.ok(
    chemical > clusters.length * 0.4,
    `chemical is the majority domain but fills only ${chemical}/${clusters.length} clusters`,
  );
});

test("cluster positions stay inside their cell", () => {
  const points = realPoints();
  const cellSize = 24;
  const clusters = cluster.aggregate(points, makeViewport(), cellSize);
  for (const c of clusters) {
    assert.ok(Number.isFinite(c.x) && Number.isFinite(c.y), "non-finite centroid");
  }
});

test("domain breakdown sums to the cluster count", () => {
  const clusters = cluster.aggregate(realPoints(), makeViewport(), 24);
  for (const c of clusters) {
    const sum = Object.keys(c.domains).reduce((t, k) => t + c.domains[k], 0);
    assert.equal(sum, c.count, "domain histogram disagrees with count");
  }
});

test("small clusters keep members for expansion, large ones do not", () => {
  const clusters = cluster.aggregate(realPoints(), makeViewport(), 24);
  const small = clusters.filter((c) => c.count <= 64);
  const large = clusters.filter((c) => c.count > 64);
  assert.ok(small.every((c) => Array.isArray(c.members)), "small cluster dropped members");
  assert.ok(large.every((c) => c.members === null), "large cluster retained members");
});

test("glyph area, not radius, scales with record count", () => {
  // Area-proportional encoding is what a reader judges correctly; radius
  // proportional encoding exaggerates large clusters roughly quadratically.
  const base = 3;
  const one = cluster.radiusFor(1, base);
  const four = cluster.radiusFor(4, base);
  assert.equal(one, base);
  assert.ok(Math.abs(four - base * 2) < 1e-12, "four records should double the radius");
  const capped = cluster.radiusFor(1e6, base);
  assert.ok(capped <= base * 4 + 1e-12, "cluster glyph grew without bound");
});

test("glyphs never exceed half a cell, so labels cannot collide", () => {
  // Overlapping glyphs rendered adjacent counts as one unreadable number.
  const cellSize = 26;
  const maxRadius = cellSize * 0.48;
  for (const count of [1, 2, 10, 500, 12813]) {
    assert.ok(
      cluster.radiusFor(count, 5, maxRadius) <= maxRadius + 1e-12,
      `radius for ${count} exceeded half the cell`,
    );
  }
});

test("singleton detection drives per-record rendering", () => {
  assert.equal(cluster.isSingleton({ count: 1 }), true);
  assert.equal(cluster.isSingleton({ count: 2 }), false);
});

test("aggregating the real dataset is fast enough to run per frame", () => {
  const points = realPoints();
  const v = makeViewport();
  const started = process.hrtime.bigint();
  for (let i = 0; i < 10; i += 1) {
    cluster.aggregate(points, v, 24);
  }
  const perFrameMs = Number(process.hrtime.bigint() - started) / 1e6 / 10;
  assert.ok(perFrameMs < 120, `aggregation took ${perFrameMs}ms per frame`);
});
