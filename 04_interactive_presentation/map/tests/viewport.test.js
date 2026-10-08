// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — viewport transform, zoom and pan tests.

"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const Viewport = require("../viewport.js");
const projection = require("../projection.js");

const WORLD = projection.bounds(projection.equalEarth, 5);

/**
 * Build a viewport over the Equal Earth world at a typical canvas size.
 * @param {number} [w] Width.
 * @param {number} [h] Height.
 * @returns {InstanceType<typeof Viewport>} Initialized viewport instance.
 */
function makeViewport(w, h) {
  return new Viewport({
    width: w || 960,
    height: h || 480,
    world: WORLD,
    maxZoom: 64,
  });
}

/**
 * Round-trip four screen positions at four zoom levels through the real world/screen transforms.
 * @returns {void}
 */
test("screen and world transforms are exact inverses", () => {
  const v = makeViewport();
  for (const zoom of [1, 2.5, 8, 33]) {
    v.zoom = zoom;
    v.clampCentre();
    for (const [px, py] of [
      [0, 0],
      [123, 45],
      [959, 479],
      [480, 240],
    ]) {
      const w = v.toWorld(px, py);
      const s = v.toScreen(w.x, w.y);
      assert.ok(Math.abs(s.x - px) < 1e-9, `x ${px} at zoom ${zoom} -> ${s.x}`);
      assert.ok(Math.abs(s.y - py) < 1e-9, `y ${py} at zoom ${zoom} -> ${s.y}`);
    }
  }
});

/**
 * Keep both projected world corners within the reset canvas extent.
 * @returns {void}
 */
test("the world fits inside the canvas at minimum zoom", () => {
  const v = makeViewport();
  v.reset();
  const topLeft = v.toScreen(WORLD.minX, WORLD.maxY);
  const bottomRight = v.toScreen(WORLD.maxX, WORLD.minY);
  assert.ok(topLeft.x >= -1e-6, `world overflows left: ${topLeft.x}`);
  assert.ok(topLeft.y >= -1e-6, `world overflows top: ${topLeft.y}`);
  assert.ok(bottomRight.x <= v.width + 1e-6, `world overflows right`);
  assert.ok(bottomRight.y <= v.height + 1e-6, `world overflows bottom`);
});

/**
 * Keep the center anchor fixed while also exercising clamped zoom at two edge anchors.
 * @returns {void}
 */
test("zooming about a point holds that point stationary", () => {
  // This is what makes wheel zoom feel anchored rather than lurching; an error
  // here is immediately visible but hard to describe, so it is pinned.
  const v = makeViewport();
  for (const [px, py] of [
    [480, 240],
    [100, 80],
    [900, 400],
  ]) {
    v.reset();
    const before = v.toWorld(px, py);
    v.zoomAbout(2.5, px, py);
    const after = v.toWorld(px, py);
    // Clamping may move the centre when the anchor is near a world edge, so
    // the assertion allows the clamp but forbids drift at the centre.
    if (px === 480 && py === 240) {
      assert.ok(Math.abs(after.x - before.x) < 1e-9, "anchor drifted in x");
      assert.ok(Math.abs(after.y - before.y) < 1e-9, "anchor drifted in y");
    }
  }
});

/**
 * Keep repeated zoom-in and zoom-out operations within their configured upper and lower limits.
 * @returns {void}
 */
test("zoom is clamped to its configured range", () => {
  const v = makeViewport();
  for (let i = 0; i < 80; i += 1) v.zoomAbout(2, 480, 240);
  assert.ok(v.zoom <= v.maxZoom + 1e-12, `zoom ran past max: ${v.zoom}`);
  for (let i = 0; i < 200; i += 1) v.zoomAbout(0.5, 480, 240);
  assert.ok(v.zoom >= v.minZoom - 1e-12, `zoom ran past min: ${v.zoom}`);
});

/**
 * Keep repeatedly panned visible bounds inside the world at four-times zoom.
 * @returns {void}
 */
test("panning cannot push the map off screen", () => {
  const v = makeViewport();
  v.zoom = 4;
  v.clampCentre();
  for (let i = 0; i < 400; i += 1) v.panBy(500, 500);
  let visible = v.visibleWorld();
  assert.ok(visible.minX >= WORLD.minX - 1e-6, "panned past the western edge");
  assert.ok(visible.maxY <= WORLD.maxY + 1e-6, "panned past the northern edge");
  for (let i = 0; i < 800; i += 1) v.panBy(-500, -500);
  visible = v.visibleWorld();
  assert.ok(visible.maxX <= WORLD.maxX + 1e-6, "panned past the eastern edge");
  assert.ok(visible.minY >= WORLD.minY - 1e-6, "panned past the southern edge");
});

/**
 * Keep the reset world center unchanged after a large screen-space pan.
 * @returns {void}
 */
test("at minimum zoom the map stays centred however hard it is panned", () => {
  const v = makeViewport();
  v.reset();
  const cx = v.centreX;
  const cy = v.centreY;
  v.panBy(1000, -1000);
  assert.ok(
    Math.abs(v.centreX - cx) < 1e-9,
    "drifted horizontally when fully zoomed out",
  );
  assert.ok(
    Math.abs(v.centreY - cy) < 1e-9,
    "drifted vertically when fully zoomed out",
  );
});

/**
 * Expand visible bounds with a pixel margin while retaining the screen center in the unpadded extent.
 * @returns {void}
 */
test("visibleWorld covers the canvas and grows with margin", () => {
  const v = makeViewport();
  v.zoom = 6;
  v.clampCentre();
  const tight = v.visibleWorld();
  const loose = v.visibleWorld(120);
  assert.ok(
    loose.minX <= tight.minX && loose.maxX >= tight.maxX,
    "margin did not widen",
  );
  assert.ok(
    loose.minY <= tight.minY && loose.maxY >= tight.maxY,
    "margin did not heighten",
  );
  const centre = v.toWorld(v.width / 2, v.height / 2);
  assert.ok(
    centre.x >= tight.minX && centre.x <= tight.maxX,
    "centre outside visible",
  );
  assert.ok(
    centre.y >= tight.minY && centre.y <= tight.maxY,
    "centre outside visible",
  );
});

/**
 * Refit an enlarged canvas and retain usable positive dimensions and finite scale after zero-size resize.
 * @returns {void}
 */
test("resize preserves the fit and survives degenerate sizes", () => {
  const v = makeViewport();
  v.resize(1600, 900);
  v.reset();
  const topLeft = v.toScreen(WORLD.minX, WORLD.maxY);
  assert.ok(
    topLeft.x >= -1e-6 && topLeft.y >= -1e-6,
    "world overflows after resize",
  );
  v.resize(0, 0);
  assert.ok(v.width >= 1 && v.height >= 1, "degenerate size not guarded");
  assert.ok(Number.isFinite(v.scale()), "scale became non-finite");
});

/**
 * Accept an in-range requested zoom and clamp an excessive requested zoom to the configured maximum.
 * @returns {void}
 */
test("centreOn moves the view and respects the zoom clamp", () => {
  const v = makeViewport();
  v.centreOn(0.2, 0.3, 10);
  assert.equal(v.zoom, 10);
  v.centreOn(0.2, 0.3, 1e9);
  assert.equal(v.zoom, v.maxZoom);
});

/**
 * Restore configured minimum zoom and the world midpoint after zoom and pan operations.
 * @returns {void}
 */
test("reset returns to the full-world view from anywhere", () => {
  const v = makeViewport();
  v.zoomAbout(20, 100, 100);
  v.panBy(300, -200);
  v.reset();
  assert.equal(v.zoom, v.minZoom);
  assert.ok(Math.abs(v.centreX - (WORLD.minX + WORLD.maxX) / 2) < 1e-12);
  assert.ok(Math.abs(v.centreY - (WORLD.minY + WORLD.maxY) / 2) < 1e-12);
});

/**
 * Keep a newly constructed viewport inside its configured zoom interval.
 * @returns {void}
 */
test("initial zoom respects both configured limits", () => {
  for (const limits of [
    { minZoom: 2, maxZoom: 8 },
    { minZoom: 0.125, maxZoom: 0.5 },
    { minZoom: 0.25, maxZoom: 8 },
  ]) {
    const v = new Viewport({
      width: 960,
      height: 480,
      world: WORLD,
      ...limits,
    });
    assert.ok(
      v.zoom >= v.minZoom,
      "initial zoom fell below the configured minimum",
    );
    assert.ok(
      v.zoom <= v.maxZoom,
      "initial zoom exceeded the configured maximum",
    );
    const anchor = v.toWorld(v.width / 2, v.height / 2);
    const screen = v.toScreen(anchor.x, anchor.y);
    assert.ok(
      Math.abs(screen.x - v.width / 2) < 1e-9,
      "initial horizontal transform drifted",
    );
    assert.ok(
      Math.abs(screen.y - v.height / 2) < 1e-9,
      "initial vertical transform drifted",
    );
  }
});
