// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — real Cairo canvas painting and refusal contracts.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const { mount } = require("./native-map-fixture.cjs");
const renderer = require("../renderer.js"),
  projection = require("../projection.js"),
  cluster = require("../cluster.js");
test("native raster painting retains state, real pixels and the actual cluster input", (context) => {
  const { canvas, engine } = mount(context),
    ctx = canvas.getContext("2d");
  assert.ok(ctx);
  ctx.fillStyle = "#123456";
  renderer.drawBackground(ctx, engine.viewport);
  assert.equal(ctx.fillStyle, "#123456");
  assert.deepEqual(
    Array.from(ctx.getImageData(0, 0, 1, 1).data),
    [16, 35, 31, 255],
  );
  renderer.drawLand(ctx, engine.viewport, projection.equalEarth, [
    [
      [0, 0],
      [10, 0],
      [10, 10],
    ],
  ]);
  const cells = [
    { x: 10, y: 10, count: 1, domain: "fission" },
    { x: 30, y: 10, count: 2, domain: "chemical" },
    { x: 50, y: 10, count: 400, domain: "chemical", accent: "fusion" },
    { x: 70, y: 10, count: 1, domain: "unregistered" },
  ];
  const before = structuredClone(cells);
  renderer.drawClusters(ctx, cells, { radiusFor: cluster.radiusFor });
  renderer.drawClusters(ctx, cells, {
    radiusFor: cluster.radiusFor,
    order: ["fusion", "fission"],
  });
  renderer.drawClusterLabels(ctx, cells, cluster.radiusFor);
  renderer.drawFocus(ctx, null, cluster.radiusFor);
  renderer.drawFocus(ctx, cells[0], cluster.radiusFor);
  Reflect.apply(renderer.drawClusters, undefined, [ctx, [], null]);
  assert.deepEqual(cells, before);
  assert.equal(ctx.fillStyle, "#123456");
  assert.equal(ctx.globalAlpha, 1);
  assert.ok(canvas.toDataURL().startsWith("data:image/png;base64,"));
  assert.equal(renderer.formatCount(1000), "1k");
  assert.equal(renderer.formatCount(999), "999");
  for (const domain of [
    null,
    undefined,
    "",
    "constructor",
    "__proto__",
    "absent",
  ])
    assert.equal(renderer.domainColour(domain), renderer.THEME.domains.unknown);
});
test("native graticule defaults are pixel-identical and invalid spacing refuses before painting", (context) => {
  const { canvas, engine } = mount(context),
    ctx = canvas.getContext("2d");
  assert.ok(ctx);
  renderer.drawBackground(ctx, engine.viewport);
  renderer.drawGraticule(ctx, engine.viewport, projection.equalEarth, 30);
  const reference = canvas.toDataURL();
  for (const step of [undefined, 0, null]) {
    renderer.drawBackground(ctx, engine.viewport);
    renderer.drawGraticule(ctx, engine.viewport, projection.equalEarth, step);
    assert.equal(canvas.toDataURL(), reference);
  }
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
    assert.throws(
      () =>
        Reflect.apply(renderer.drawGraticule, undefined, [
          ctx,
          engine.viewport,
          projection.equalEarth,
          step,
        ]),
      RangeError,
    );
    assert.equal(canvas.toDataURL(), reference);
  }
});
