// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — quadtree tests, checked against brute force and real data.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Quadtree = require("../quadtree.js");
const projection = require("../projection.js");
require("../../application-data.js");

const DATA = path.join(
  __dirname,
  "..",
  "..",
  "data",
  "global_reactors.sample.json",
);

/**
 * Project every shipped facility with a usable coordinate.
 * @returns {Array<{x: number, y: number, id: string}>} Projected points.
 * @throws {Error} A consumed original dataset cell or coordinate fails public admission.
 */
function realFacilityPoints() {
  // Datasets are published as a document whose `records` array carries the
  // rows; older exports were bare arrays. Accept both, so the tests read the
  // real shipped file whichever form it is in.
  /** @type {unknown} */
  const document = JSON.parse(fs.readFileSync(DATA, "utf8"));
  const rows = globalThis.AtlasApplicationData.facilities(document);
  const proj = projection.equalEarth;
  const points = [];
  for (const row of rows) {
    const lon = Number(row.lon);
    const lat = Number(row.lat);
    if (!Number.isFinite(lon) || !Number.isFinite(lat)) continue;
    if (row.lon === null || row.lat === null) continue;
    const xy = proj.forward(lon, lat);
    points.push({ x: xy.x, y: xy.y, id: row.id });
  }
  return points;
}

/**
 * Deterministic pseudo-random generator, so failures reproduce exactly.
 * @param {number} seed Initial state.
 * @returns {function(): number} Generator yielding values in [0, 1).
 */
function rng(seed) {
  let state = seed >>> 0;
  /**
   * Advance the seeded 32-bit linear-congruential state and scale it into [0, 1).
   * @returns {number} Next reproducible fractional sample.
   */
  return function next() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

/**
 * Refuse null bounds and rectangles with zero width or height using the production constructor.
 * @returns {void}
 */
test("rejects degenerate bounds instead of indexing into nothing", () => {
  assert.throws(() => new Quadtree(null), /non-degenerate/);
  assert.throws(
    () => new Quadtree({ minX: 0, minY: 0, maxX: 0, maxY: 1 }),
    /non-degenerate/,
  );
  assert.throws(
    () => new Quadtree({ minX: 0, minY: 1, maxX: 1, maxY: 1 }),
    /non-degenerate/,
  );
});

/**
 * Retrieve all 5000 deterministic random points and preserve their unique identifiers after subdivision.
 * @returns {void}
 */
test("every inserted point is retrievable — none are lost to subdivision", () => {
  const next = rng(20260929);
  const points = [];
  for (let i = 0; i < 5000; i += 1) {
    points.push({ x: next() * 200 - 100, y: next() * 100 - 50, id: i });
  }
  const tree = Quadtree.build(points);
  assert.equal(tree.size, points.length, "tree size disagrees with input");
  const all = tree.query({ minX: -1e9, minY: -1e9, maxX: 1e9, maxY: 1e9 });
  assert.equal(all.length, points.length, "range query lost points");
  assert.equal(
    new Set(
      all.map(
        /**
         * Read the original numeric identifier from a retrieved or expected point.
         * @param {{x: number, y: number, id: number}} p Original random-data point.
         * @returns {number} Identifier used to compare complete result sets.
         */
        (p) => p.id,
      ),
    ).size,
    points.length,
    "duplicates",
  );
});

/**
 * Keep all 500 distinct records sharing one planar coordinate in the populated index.
 * @returns {void}
 */
test("coincident points all survive rather than collapsing", () => {
  // Real registers contain many records sharing one coordinate; a tree that
  // subdivides forever or overwrites duplicates would silently drop them.
  const points = [];
  for (let i = 0; i < 500; i += 1) {
    points.push({ x: 5, y: 5, id: i });
  }
  const tree = Quadtree.build(points);
  assert.equal(tree.size, 500);
  const found = tree.query({ minX: 4, minY: 4, maxX: 6, maxY: 6 });
  assert.equal(found.length, 500);
});

/**
 * Compare forty indexed rectangle queries with complete scans of the same 2000 points.
 * @returns {void}
 */
test("range queries agree with brute force on random data", () => {
  const next = rng(7);
  const points = [];
  for (let i = 0; i < 2000; i += 1) {
    points.push({ x: next() * 20 - 10, y: next() * 20 - 10, id: i });
  }
  const tree = Quadtree.build(points);
  for (let trial = 0; trial < 40; trial += 1) {
    const minX = next() * 18 - 10;
    const minY = next() * 18 - 10;
    const range = {
      minX,
      minY,
      maxX: minX + next() * 6,
      maxY: minY + next() * 6,
    };
    const expected = points
      .filter(
        /**
         * Select the brute-force expected points using inclusive rectangle boundaries.
         * @param {{x: number, y: number, id: number}} p Original random-data point.
         * @returns {boolean} Whether this point lies inside the query rectangle.
         */
        (p) =>
          p.x >= range.minX &&
          p.x <= range.maxX &&
          p.y >= range.minY &&
          p.y <= range.maxY,
      )
      .map(
        /**
         * Read the original numeric identifier from a retrieved or expected point.
         * @param {{x: number, y: number, id: number}} p Original random-data point.
         * @returns {number} Identifier used to compare complete result sets.
         */
        (p) => p.id,
      )
      .sort(
        /**
         * Order numeric point identifiers for exact indexed-versus-scan comparison.
         * @param {number} a First identifier.
         * @param {number} b Second identifier.
         * @returns {number} Signed numeric ordering difference.
         */
        (a, b) => a - b,
      );
    const actual = tree
      .query(range)
      .map(
        /**
         * Read the original numeric identifier from a retrieved or expected point.
         * @param {{x: number, y: number, id: number}} p Original random-data point.
         * @returns {number} Identifier used to compare complete result sets.
         */
        (p) => p.id,
      )
      .sort(
        /**
         * Order numeric point identifiers for exact indexed-versus-scan comparison.
         * @param {number} a First identifier.
         * @param {number} b Second identifier.
         * @returns {number} Signed numeric ordering difference.
         */
        (a, b) => a - b,
      );
    assert.deepEqual(
      actual,
      expected,
      `range query mismatch on trial ${trial}`,
    );
  }
});

/**
 * Compare sixty radius-limited nearest queries with complete scans, including empty neighborhoods.
 * @returns {void}
 */
test("nearest agrees with brute force, including when nothing is in range", () => {
  const next = rng(99);
  const points = [];
  for (let i = 0; i < 1500; i += 1) {
    points.push({ x: next() * 20 - 10, y: next() * 20 - 10, id: i });
  }
  const tree = Quadtree.build(points);
  for (let trial = 0; trial < 60; trial += 1) {
    const qx = next() * 24 - 12;
    const qy = next() * 24 - 12;
    const radius = 0.05 + next() * 2;
    let best = null;
    let bestD2 = radius * radius;
    for (const p of points) {
      const d2 = (p.x - qx) ** 2 + (p.y - qy) ** 2;
      if (d2 <= bestD2) {
        bestD2 = d2;
        best = p;
      }
    }
    const actual = tree.nearest(qx, qy, radius);
    if (best === null) {
      assert.equal(actual, null, "expected no hit within radius");
    } else {
      assert.ok(actual, "expected a hit");
      const actualD2 = (actual.x - qx) ** 2 + (actual.y - qy) ** 2;
      assert.ok(
        Math.abs(actualD2 - bestD2) < 1e-12,
        `nearest picked a farther point on trial ${trial}`,
      );
    }
  }
});

/**
 * Create an empty bulk-built index whose rectangle and nearest queries remain empty.
 * @returns {void}
 */
test("an empty build yields a usable, empty tree", () => {
  const tree = Quadtree.build([]);
  assert.equal(tree.size, 0);
  assert.deepEqual(
    tree.query({ minX: -1e9, minY: -1e9, maxX: 1e9, maxY: 1e9 }),
    [],
  );
  assert.equal(tree.nearest(0, 0, 10), null);
});

/**
 * Return no rectangle or nearest match for query regions far outside the indexed point.
 * @returns {void}
 */
test("queries outside the indexed region return nothing", () => {
  const tree = Quadtree.build([{ x: 0, y: 0, id: 1 }]);
  assert.deepEqual(
    tree.query({ minX: 100, minY: 100, maxX: 200, maxY: 200 }),
    [],
  );
  assert.equal(tree.nearest(100, 100, 1), null);
});

/**
 * Index every usable coordinate from the shipped facility file and retrieve the same record count.
 * @returns {void}
 */
test("indexes the real facility dataset without losing records", () => {
  const points = realFacilityPoints();
  assert.ok(
    points.length > 12000,
    `expected the full dataset, got ${points.length}`,
  );
  const tree = Quadtree.build(points);
  assert.equal(tree.size, points.length);
  const all = tree.query({ minX: -1e9, minY: -1e9, maxX: 1e9, maxY: 1e9 });
  assert.equal(
    all.length,
    points.length,
    "real dataset lost points in the index",
  );
});

/**
 * Compare twenty-five nearest probes of shipped facility points with complete planar-distance scans.
 * @returns {void}
 */
test("hit testing the real dataset matches brute force", () => {
  const points = realFacilityPoints();
  const tree = Quadtree.build(points);
  const next = rng(4242);
  for (let trial = 0; trial < 25; trial += 1) {
    const probe = points[Math.floor(next() * points.length)];
    const radius = 0.01;
    let bestD2 = radius * radius;
    for (const p of points) {
      const d2 = (p.x - probe.x) ** 2 + (p.y - probe.y) ** 2;
      if (d2 <= bestD2) {
        bestD2 = d2;
      }
    }
    const actual = tree.nearest(probe.x, probe.y, radius);
    assert.ok(actual, "expected to hit at least the probe point itself");
    const actualD2 = (actual.x - probe.x) ** 2 + (actual.y - probe.y) ** 2;
    assert.ok(
      Math.abs(actualD2 - bestD2) < 1e-12,
      "real-data nearest mismatch",
    );
  }
});

/**
 * Build the shipped facility index and perform 500 hit tests within the existing two-second limit.
 * @returns {void}
 */
test("indexing the real dataset is fast enough for interactive use", () => {
  // The engine rebuilds the index when filters change, which happens while the
  // user is typing; a regression to a linear structure would show up here.
  const points = realFacilityPoints();
  const started = process.hrtime.bigint();
  const tree = Quadtree.build(points);
  for (let i = 0; i < 500; i += 1) {
    tree.nearest(points[i].x, points[i].y, 0.02);
  }
  const elapsedMs = Number(process.hrtime.bigint() - started) / 1e6;
  assert.ok(
    elapsedMs < 2000,
    `index build and 500 hit tests took ${elapsedMs}ms`,
  );
});
