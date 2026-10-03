// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — coastline recovery tests against the shipped basemap.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const coastline = require("../coastline.js");

const INDEX = path.join(__dirname, "..", "..", "index.html");

/**
 * Extract the shipped basemap path data from the production index page.
 *
 * @returns {string} The land path's ``d`` attribute.
 */
function shippedPathData() {
  const html = fs.readFileSync(INDEX, "utf8");
  const match = html.match(/class="land"[\s\S]*?d="([^"]+)"/);
  assert.ok(match, "basemap land path not found in index.html");
  return match[1];
}

test("the shipped basemap parses into rings", () => {
  const rings = coastline.parsePath(shippedPathData());
  assert.ok(rings.length > 100, `expected many rings, got ${rings.length}`);
  for (const ring of rings) {
    assert.ok(ring.length >= 3, "ring with fewer than three points survived");
  }
});

test("recovered coordinates lie inside the geographic domain", () => {
  const rings = coastline.parsePath(shippedPathData());
  const b = coastline.boundsOf(rings);
  assert.ok(b.minLon >= -180.001, `min lon ${b.minLon}`);
  assert.ok(b.maxLon <= 180.001, `max lon ${b.maxLon}`);
  assert.ok(b.minLat >= -90.001, `min lat ${b.minLat}`);
  assert.ok(b.maxLat <= 90.001, `max lat ${b.maxLat}`);
});

test("recovered coastline spans both hemispheres", () => {
  // A sign error in the vertical inversion would collapse the map into one
  // hemisphere while still producing in-range coordinates, so the range is
  // asserted rather than only the bounds.
  const b = coastline.boundsOf(coastline.parsePath(shippedPathData()));
  assert.ok(b.minLat < -30, `southern extent only reaches ${b.minLat}`);
  assert.ok(b.maxLat > 60, `northern extent only reaches ${b.maxLat}`);
  assert.ok(b.minLon < -100, `western extent only reaches ${b.minLon}`);
  assert.ok(b.maxLon > 100, `eastern extent only reaches ${b.maxLon}`);
});

test("latitude is not inverted — land sits where land actually is", () => {
  // Greenwich at 51.5N is land; the same longitude at 51.5S is open ocean.
  // An inverted vertical axis would swap these, which bounds checks miss.
  const rings = coastline.parsePath(shippedPathData());
  let northPoints = 0;
  let southPoints = 0;
  for (const ring of rings) {
    for (const [lon, lat] of ring) {
      if (lon > -12 && lon < 30 && lat > 35 && lat < 70) northPoints += 1;
      if (lon > -12 && lon < 30 && lat < -35 && lat > -70) southPoints += 1;
    }
  }
  assert.ok(
    northPoints > southPoints * 3,
    `European landmass not where expected (north ${northPoints}, south ${southPoints})`,
  );
});

test("corner mapping matches the plate carrée graticule exactly", () => {
  assert.deepEqual(coastline.toGeographic(0, 0), [-180, 90]);
  assert.deepEqual(coastline.toGeographic(1000, 500), [180, -90]);
  assert.deepEqual(coastline.toGeographic(500, 250), [0, 0]);
});

test("custom view dimensions are honoured", () => {
  assert.deepEqual(coastline.toGeographic(0, 0, 360, 180), [-180, 90]);
  assert.deepEqual(coastline.toGeographic(360, 180, 360, 180), [180, -90]);
});

test("simple paths parse into the expected rings", () => {
  const rings = coastline.parsePath("M500,250L600,250L600,300Z M0,0L100,0L100,50Z");
  assert.equal(rings.length, 2);
  assert.equal(rings[0].length, 3);
  assert.deepEqual(rings[0][0], [0, 0]);
});

test("degenerate rings are discarded", () => {
  const rings = coastline.parsePath("M500,250L600,250Z M0,0L100,0L100,50Z");
  assert.equal(rings.length, 1, "two-point ring should not survive");
});

test("malformed and unsupported input is rejected, not silently mangled", () => {
  assert.throws(() => coastline.parsePath(""), /empty path data/);
  assert.throws(() => coastline.parsePath("   "), /empty path data/);
  assert.throws(() => coastline.parsePath(null), /empty path data/);
  // Bezier curves would be silently dropped by a lenient parser, quietly
  // deforming the coastline.
  assert.throws(
    () => coastline.parsePath("M0,0C10,10 20,20 30,30Z"),
    /unsupported path command/,
  );
  assert.throws(
    () => coastline.parsePath("L10,10"),
    /line command before any move/,
  );
});

test("fromDocument reads a basemap out of a DOM-like document", () => {
  const data = shippedPathData();
  const fakeDoc = {
    querySelector(selector) {
      return selector === "path.land"
        ? { getAttribute: () => data }
        : null;
    },
  };
  const rings = coastline.fromDocument(fakeDoc);
  assert.ok(rings.length > 100);
  assert.throws(
    () => coastline.fromDocument({ querySelector: () => null }),
    /basemap path not found/,
  );
});

test("round-trip through the projection preserves the coastline", () => {
  // Recovering geography then reprojecting must be lossless, otherwise the
  // reprojected basemap would drift away from the facility points drawn on it.
  const projection = require("../projection.js");
  const rings = coastline.parsePath(shippedPathData());
  const p = projection.plateCarree;
  let worst = 0;
  for (const ring of rings.slice(0, 20)) {
    for (const [lon, lat] of ring) {
      const xy = p.forward(lon, lat);
      const back = p.inverse(xy.x, xy.y);
      worst = Math.max(worst, Math.abs(back.lon - lon), Math.abs(back.lat - lat));
    }
  }
  assert.ok(worst < 1e-10, `coastline round-trip drifted by ${worst}`);
});
