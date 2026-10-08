// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — projection behaviour tests.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const projection = require("../projection.js");

const DEG = Math.PI / 180;

/** Latitudes and longitudes that exercise poles, equator, antimeridian and mid-latitudes. */
const LATS = [-89.9, -75, -45, -23.5, 0, 23.5, 45, 66.5, 75, 89.9];
const LONS = [-179.9, -120, -60, -1, 0, 1, 60, 120, 179.9];

/**
 * Round-trip the complete latitude/longitude grid within 1e-12 degrees.
 * @returns {void}
 */
test("plate carrée is exactly invertible", () => {
  const p = projection.plateCarree;
  for (const lat of LATS) {
    for (const lon of LONS) {
      const xy = p.forward(lon, lat);
      const back = p.inverse(xy.x, xy.y);
      assert.ok(Math.abs(back.lon - lon) < 1e-12, `lon ${lon} -> ${back.lon}`);
      assert.ok(Math.abs(back.lat - lat) < 1e-12, `lat ${lat} -> ${back.lat}`);
    }
  }
});

/**
 * Round-trip the same geographic grid through Equal Earth within 1e-9 degrees.
 * @returns {void}
 */
test("equal earth round-trips to double precision", () => {
  const p = projection.equalEarth;
  for (const lat of LATS) {
    for (const lon of LONS) {
      const xy = p.forward(lon, lat);
      const back = p.inverse(xy.x, xy.y);
      assert.ok(Math.abs(back.lat - lat) < 1e-9, `lat ${lat} -> ${back.lat}`);
      assert.ok(Math.abs(back.lon - lon) < 1e-9, `lon ${lon} -> ${back.lon}`);
    }
  }
});

/**
 * Compare the finite-difference area Jacobian with cosine latitude across the graticule.
 * @returns {void}
 */
test("equal earth preserves area — Jacobian equals cos(lat) everywhere", () => {
  // The defining property of an equal-area projection: the determinant of the
  // Jacobian d(x,y)/d(lon,lat) must equal cos(lat) at every point. This is the
  // check that would fail if the easting denominator were not exactly the
  // derivative of the northing polynomial.
  const p = projection.equalEarth;
  const h = 1e-6;
  let worst = 0;
  for (let lat = -85; lat <= 85; lat += 5) {
    for (let lon = -170; lon <= 170; lon += 10) {
      const dx = p.forward(lon + h, lat);
      const dx0 = p.forward(lon - h, lat);
      const dy = p.forward(lon, lat + h);
      const dy0 = p.forward(lon, lat - h);
      const dxdlon = (dx.x - dx0.x) / (2 * h * DEG);
      const dydlon = (dx.y - dx0.y) / (2 * h * DEG);
      const dxdlat = (dy.x - dy0.x) / (2 * h * DEG);
      const dydlat = (dy.y - dy0.y) / (2 * h * DEG);
      const jacobian = Math.abs(dxdlon * dydlat - dxdlat * dydlon);
      const expected = Math.cos(lat * DEG);
      worst = Math.max(worst, Math.abs(jacobian - expected));
    }
  }
  assert.ok(
    worst < 1e-6,
    `worst Jacobian deviation ${worst} exceeds tolerance`,
  );
});

/**
 * Keep the two public area-preservation flags consistent with their projection roles.
 * @returns {void}
 */
test("plate carrée is declared non-equal-area and equal earth equal-area", () => {
  assert.equal(projection.plateCarree.equalArea, false);
  assert.equal(projection.equalEarth.equalArea, true);
});

/**
 * Show the equirectangular Jacobian differs from equal-area behavior at 60 degrees north.
 * @returns {void}
 */
test("plate carrée is NOT equal-area — guards against a mislabelled projection", () => {
  // Confirms the equalArea flags above are describing real behaviour rather
  // than being decorative metadata that could drift from the maths.
  const p = projection.plateCarree;
  const h = 1e-6;
  const lat = 60;
  const dx = p.forward(1 + h, lat);
  const dx0 = p.forward(1 - h, lat);
  const dy = p.forward(1, lat + h);
  const dy0 = p.forward(1, lat - h);
  const jacobian = Math.abs(
    ((dx.x - dx0.x) / (2 * h * DEG)) * ((dy.y - dy0.y) / (2 * h * DEG)) -
      ((dy.x - dy0.x) / (2 * h * DEG)) * ((dx.y - dx0.y) / (2 * h * DEG)),
  );
  assert.ok(
    Math.abs(jacobian - Math.cos(lat * DEG)) > 0.1,
    "plate carrée unexpectedly behaved as equal-area",
  );
});

/**
 * Preserve north/south and east/west symmetry at the sampled geographic coordinates.
 * @returns {void}
 */
test("equal earth is symmetric about equator and prime meridian", () => {
  const p = projection.equalEarth;
  for (const lat of [10, 40, 70]) {
    for (const lon of [30, 90, 150]) {
      const north = p.forward(lon, lat);
      const south = p.forward(lon, -lat);
      const west = p.forward(-lon, lat);
      assert.ok(Math.abs(north.y + south.y) < 1e-12, "north/south asymmetry");
      assert.ok(Math.abs(north.x - south.x) < 1e-12, "north/south x mismatch");
      assert.ok(Math.abs(north.x + west.x) < 1e-12, "east/west asymmetry");
    }
  }
});

/**
 * Map the equator and prime meridian to the corresponding plane axes.
 * @returns {void}
 */
test("equator maps to y = 0 and prime meridian to x = 0", () => {
  for (const p of [projection.plateCarree, projection.equalEarth]) {
    assert.ok(Math.abs(p.forward(45, 0).y) < 1e-15, `${p.id} equator`);
    assert.ok(Math.abs(p.forward(0, 45).x) < 1e-15, `${p.id} meridian`);
  }
});

/**
 * Require finite nondegenerate bounds containing every sampled coordinate for both projections.
 * @returns {void}
 */
test("bounds cover the whole graticule and are finite", () => {
  for (const p of [projection.plateCarree, projection.equalEarth]) {
    const b = projection.bounds(p, 5);
    assert.ok(Number.isFinite(b.minX) && Number.isFinite(b.maxX), `${p.id} x`);
    assert.ok(Number.isFinite(b.minY) && Number.isFinite(b.maxY), `${p.id} y`);
    assert.ok(b.maxX > b.minX && b.maxY > b.minY, `${p.id} degenerate`);
    // Every sampled graticule point must fall inside the reported bounds.
    for (const lat of LATS) {
      for (const lon of LONS) {
        const q = p.forward(lon, lat);
        assert.ok(
          q.x >= b.minX - 1e-9 && q.x <= b.maxX + 1e-9,
          `${p.id} x out`,
        );
        assert.ok(
          q.y >= b.minY - 1e-9 && q.y <= b.maxY + 1e-9,
          `${p.id} y out`,
        );
      }
    }
  }
});

/**
 * Keep sampled Equal Earth world bounds within the established aspect-ratio interval.
 * @returns {void}
 */
test("equal earth is wider than tall, as the published projection is", () => {
  const b = projection.bounds(projection.equalEarth, 5);
  const ratio = (b.maxX - b.minX) / (b.maxY - b.minY);
  assert.ok(ratio > 1.8 && ratio < 2.1, `unexpected aspect ratio ${ratio}`);
});

/**
 * Resolve both registered IDs and require the authored unknown-projection error.
 * @returns {void}
 */
test("get resolves registered projections and rejects unknown ones", () => {
  assert.equal(projection.get("equal-earth").id, "equal-earth");
  assert.equal(projection.get("plate-carree").id, "plate-carree");
  assert.throws(() => projection.get("mercator"), /unknown projection/);
});

/**
 * Require enumeration to contain exactly the two registered projection identifiers.
 * @returns {void}
 */
test("list exposes every registered projection", () => {
  const ids = projection
    .list()
    .map(
      /**
       * Read the stable identifier from a registered projection.
       * @param {typeof projection.plateCarree} p Registered projection.
       * @returns {string} Stable identifier used to compare the complete registry.
       */
      (p) => p.id,
    )
    .sort();
  assert.deepEqual(ids, ["equal-earth", "plate-carree"]);
});

/**
 * Refuse every inherited Object prototype name without changing either registered projection.
 * @returns {void}
 */
test("get refuses inherited names absent from the projection registry", () => {
  for (const id of Object.getOwnPropertyNames(Object.prototype)) {
    assert.throws(() => projection.get(id), {
      name: "Error",
      message: `unknown projection: ${id}`,
    });
  }
  assert.strictEqual(projection.get("equal-earth"), projection.equalEarth);
  assert.strictEqual(projection.get("plate-carree"), projection.plateCarree);
});
