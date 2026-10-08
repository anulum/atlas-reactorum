// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native geographic, spatial and density boundary contracts.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const { mount, classic } = require("./native-map-fixture.cjs");
const projection = require("../projection.js"),
  coastline = require("../coastline.js"),
  Quadtree = require("../quadtree.js"),
  cluster = require("../cluster.js"),
  Viewport = require("../viewport.js");
test("actual source coordinates round-trip through both projections and indexed queries retain every row", (context) => {
  const { engine, rows } = mount(context);
  engine.setData(rows);
  for (const proj of projection.list()) {
    engine.setProjection(proj.id);
    const bounds = projection.bounds(proj, 30);
    assert.ok(bounds.maxX > bounds.minX && bounds.maxY > bounds.minY);
    assert.deepEqual(projection.bounds(proj, 0), projection.bounds(proj));
    for (const point of engine.points) {
      const geographic = proj.inverse(point.x, point.y);
      assert.ok(Math.abs(geographic.lon - point.lon) < 1e-8);
      assert.ok(Math.abs(geographic.lat - point.lat) < 1e-8);
    }
    const tree = Quadtree.build(engine.points, 2);
    const found = tree.query(tree.bounds);
    assert.equal(found.length, engine.points.length);
    assert.equal(new Set(found).size, engine.points.length);
    for (const point of engine.points.slice(0, 100)) {
      assert.ok(tree.nearest(point.x, point.y, 0));
    }
    assert.equal(tree.nearest(1e6, 1e6, 1), null);
    for (const range of [
      { minX: 1e6, maxX: 1e6 + 1, minY: 0, maxY: 1 },
      { minX: -1e6, maxX: -1e6 + 1, minY: 0, maxY: 1 },
      { minX: 0, maxX: 1, minY: 1e6, maxY: 1e6 + 1 },
      { minX: 0, maxX: 1, minY: -1e6, maxY: -1e6 + 1 },
    ])
      assert.deepEqual(tree.query(range), []);
    const cells = cluster.aggregate(engine.points, engine.viewport, 24);
    assert.equal(
      cells.reduce((sum, cell) => sum + cell.count, 0),
      engine.points.length,
    );
    for (const cell of cells) {
      assert.equal(
        Object.values(cell.domains).reduce((sum, n) => sum + n, 0),
        cell.count,
      );
      if (cell.members)
        assert.ok(cell.members.every((point) => engine.points.includes(point)));
    }
  }
  assert.throws(() => projection.get("absent"), /unknown projection/);
  assert.equal(Quadtree.build(null).size, 0);
  assert.equal(Quadtree.build([]).size, 0);
  assert.throws(() => new Quadtree(null), /non-degenerate/);
  assert.throws(
    () => new Quadtree({ minX: 0, maxX: 0, minY: 0, maxY: 1 }),
    /non-degenerate/,
  );
  assert.throws(
    () => new Quadtree({ minX: 0, maxX: 1, minY: 0, maxY: 0 }),
    /non-degenerate/,
  );
  const coincident = Array.from({ length: 70 }, () => ({
    ...engine.points[0],
  }));
  const tree = Quadtree.build(coincident, 1);
  assert.equal(tree.query(tree.bounds).length, 70);
  assert.equal(tree.insert({ ...coincident[0], x: 1e6 }), false);
  tree.insertIntoChild({ ...coincident[0], x: 1e6 });
  assert.equal(tree.points.at(-1)?.x, 1e6);
});
test("the original SVG coastline is recovered through a real document and malformed source paths refuse", (context) => {
  const { dom } = mount(context);
  const rings = coastline.fromDocument(dom.window.document);
  assert.ok(rings.length > 0);
  const bounds = coastline.boundsOf(rings);
  assert.ok(
    bounds.minLon < 0 &&
      bounds.maxLon > 0 &&
      bounds.minLat < 0 &&
      bounds.maxLat > 0,
  );
  assert.deepEqual(coastline.toGeographic(0, 0, 1000, 500), [-180, 90]);
  assert.deepEqual(coastline.toGeographic(0, 0), [-180, 90]);
  assert.equal(
    coastline.parsePath("m0 0 10 0 l10 10 z", { width: 20, height: 20 }).length,
    1,
  );
  assert.equal(coastline.parsePath("M0 0 L1 1 Z").length, 0);
  assert.deepEqual(coastline.parsePath(","), []);
  for (const source of [
    null,
    "",
    " ",
    "M0 0 C1 1",
    "M0",
    "M0 0 1",
    "L0 0",
    "0 0",
  ])
    assert.throws(() => coastline.parsePath(source), /coastline:/);
  assert.throws(
    () => coastline.fromDocument(dom.window.document, "#absent"),
    /path not found/,
  );
  const path = dom.window.document.querySelector("path.land");
  assert.ok(path);
  path.removeAttribute("d");
  assert.throws(
    () => coastline.fromDocument(dom.window.document),
    /empty path/,
  );
});
test("public density and viewport edge cases preserve their documented defaults", (context) => {
  const { engine } = mount(context);
  assert.throws(
    () => cluster.aggregate([], engine.viewport, 0),
    /must be positive/,
  );
  assert.equal(cluster.dominantDomain({}), "unknown");
  assert.equal(cluster.dominantDomain({ custom: 2 }), "custom");
  assert.equal(cluster.majorityDomain({}), "unknown");
  assert.equal(cluster.majorityDomain({ chemical: 2, fusion: 1 }), "chemical");
  assert.equal(cluster.accentDomain({ chemical: 2, fusion: 1 }), "fusion");
  assert.equal(cluster.accentDomain({ fusion: 1 }), null);
  assert.equal(cluster.radiusFor(1), 3);
  assert.equal(cluster.radiusFor(100, 2, 8), 8);
  assert.equal(cluster.isSingleton({ count: 1 }), true);
  assert.equal(cluster.isSingleton({ count: 2 }), false);
  const point = { x: 0, y: 0, domain: null };
  assert.equal(
    cluster.aggregate([point], engine.viewport, 24)[0].domain,
    "unknown",
  );
  for (const viewport of [
    new Viewport(),
    new Viewport(null),
    new Viewport({ width: 200, height: 100, minZoom: 2, maxZoom: 8 }),
  ]) {
    viewport.visibleWorld();
    viewport.visibleWorld(10);
    const world = viewport.toWorld(20, 30),
      screen = viewport.toScreen(world.x, world.y);
    assert.ok(Math.abs(screen.x - 20) < 1e-9 && Math.abs(screen.y - 30) < 1e-9);
    viewport.centreOn(0, 0);
    viewport.centreOn(0, 0, 4);
    viewport.panBy(1e6, 1e6);
    viewport.panBy(-1e6, -1e6);
    viewport.zoomAbout(1e6, 20, 30);
    assert.equal(viewport.zoom, viewport.maxZoom);
    viewport.zoomAbout(1e-6, 20, 30);
    assert.equal(viewport.zoom, viewport.minZoom);
    viewport.resize(0, 0);
    assert.equal(viewport.width, 1);
    assert.equal(viewport.height, 1);
    viewport.reset();
    assert.equal(viewport.zoom, viewport.minZoom);
  }
  classic(mount(context).dom);
});
test("every geometry or painter module can create its namespace in an actual fresh Window", (context) => {
  const modules = [
    "projection",
    "coastline",
    "quadtree",
    "cluster",
    "viewport",
    "renderer",
  ];
  for (const name of modules) {
    const { dom } = mount(context);
    classic(dom, [
      ...modules.filter((other) => other !== name),
      "engine",
      "interactions",
      "accessibility",
    ]);
    const namespace = dom.window.AtlasMap;
    assert.ok(namespace);
    assert.equal(Object.keys(namespace).length, 1);
  }
});
