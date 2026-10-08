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
 * @returns {string} The land path's ``d`` attribute.
 */
function shippedPathData() {
  const html = fs.readFileSync(INDEX, "utf8");
  const match = html.match(/class="land"[\s\S]*?d="([^"]+)"/);
  assert.ok(match, "basemap land path not found in index.html");
  return match[1];
}

/**
 * Parse the shipped land path into more than 100 rings with at least three vertices each.
 * @returns {void}
 */
test("the shipped basemap parses into rings", () => {
  const rings = coastline.parsePath(shippedPathData());
  assert.ok(rings.length > 100, `expected many rings, got ${rings.length}`);
  for (const ring of rings) {
    assert.ok(ring.length >= 3, "ring with fewer than three points survived");
  }
});

/**
 * Keep every recovered geographic extent within the longitude and latitude domain tolerances.
 * @returns {void}
 */
test("recovered coordinates lie inside the geographic domain", () => {
  const rings = coastline.parsePath(shippedPathData());
  const b = coastline.boundsOf(rings);
  assert.ok(b.minLon >= -180.001, `min lon ${b.minLon}`);
  assert.ok(b.maxLon <= 180.001, `max lon ${b.maxLon}`);
  assert.ok(b.minLat >= -90.001, `min lat ${b.minLat}`);
  assert.ok(b.maxLat <= 90.001, `max lat ${b.maxLat}`);
});

/**
 * Require the shipped basemap to extend north, south, east and west beyond the asserted limits.
 * @returns {void}
 */
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

/**
 * Require northern European vertices to outnumber the corresponding southern region by more than three.
 * @returns {void}
 */
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

/**
 * Invert the default viewBox corners and center to their exact geographic coordinate pairs.
 * @returns {void}
 */
test("corner mapping matches the plate carrée graticule exactly", () => {
  assert.deepEqual(coastline.toGeographic(0, 0), [-180, 90]);
  assert.deepEqual(coastline.toGeographic(1000, 500), [180, -90]);
  assert.deepEqual(coastline.toGeographic(500, 250), [0, 0]);
});

/**
 * Invert both corners of the explicitly supplied 360 by 180 viewBox.
 * @returns {void}
 */
test("custom view dimensions are honoured", () => {
  assert.deepEqual(coastline.toGeographic(0, 0, 360, 180), [-180, 90]);
  assert.deepEqual(coastline.toGeographic(360, 180, 360, 180), [180, -90]);
});

/**
 * Recover two absolute move/line/close paths and verify the first ring and center coordinate.
 * @returns {void}
 */
test("simple paths parse into the expected rings", () => {
  const rings = coastline.parsePath(
    "M500,250L600,250L600,300Z M0,0L100,0L100,50Z",
  );
  assert.equal(rings.length, 2);
  assert.equal(rings[0].length, 3);
  assert.deepEqual(rings[0][0], [0, 0]);
});

/**
 * Discard the two-vertex path while retaining the adjacent three-vertex coastline ring.
 * @returns {void}
 */
test("degenerate rings are discarded", () => {
  const rings = coastline.parsePath("M500,250L600,250Z M0,0L100,0L100,50Z");
  assert.equal(rings.length, 1, "two-point ring should not survive");
});

/**
 * Refuse empty, non-string, unsupported-curve and line-before-move inputs with their specific errors.
 * @returns {void}
 */
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

/**
 * Read shipped geometry through the existing DOM-like adapter and refuse its absent-land-path case.
 * @returns {void}
 */
test("fromDocument reads a basemap out of a DOM-like document", () => {
  const data = shippedPathData();
  const fakeDoc = {
    /**
     * Select the shipped land path for the existing document-access boundary test.
     * @param {string} selector Selector supplied by the production coastline reader.
     * @returns {{getAttribute: () => string}|null} Captured land data only for the expected selector.
     */
    querySelector(selector) {
      return selector === "path.land"
        ? {
            /**
             * Return the path attribute read from the shipped index page.
             * @returns {string} Original land geometry captured before document lookup.
             */
            getAttribute: () => data,
          }
        : null;
    },
  };
  const rings = coastline.fromDocument(fakeDoc);
  assert.ok(rings.length > 100);
  assert.throws(
    () =>
      coastline.fromDocument({
        /**
         * Report the absence of a land path to exercise the production reader's refusal.
         * @returns {null} Missing selected node.
         */
        querySelector: () => null,
      }),
    /basemap path not found/,
  );
});

/**
 * Round-trip the first twenty shipped rings through Plate carrée within 1e-10 degrees.
 * @returns {void}
 */
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
      worst = Math.max(
        worst,
        Math.abs(back.lon - lon),
        Math.abs(back.lat - lat),
      );
    }
  }
  assert.ok(worst < 1e-10, `coastline round-trip drifted by ${worst}`);
});
