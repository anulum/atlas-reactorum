// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual map pointer and keyboard input paths.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm");
const { mount, classic } = require("./native-map-fixture.cjs");
test("every actual keyboard path retains original focus and default cancellation", (context) => {
  /** @type {import("../../application-data.js").ApplicationFacility[]} */
  const selected = [];
  const { engine, canvas, rows, dom } = mount(context, {
    /**
     * Retain the actual original row emitted by native activation.
     * @param {import("../../application-data.js").ApplicationFacility} row Original selected source row.
     * @returns {number} Number of retained original emissions.
     */
    onSelect: (row) => selected.push(row),
  });
  engine.setData(
    rows.filter((row) => row.lat !== null && row.lon !== null).slice(0, 1),
  );
  for (const shiftKey of [false, true])
    for (const key of [
      "ArrowLeft",
      "ArrowRight",
      "ArrowUp",
      "ArrowDown",
      "+",
      "=",
      "-",
      "_",
      "0",
      "Enter",
      " ",
    ]) {
      const event = new dom.window.KeyboardEvent("keydown", {
        key,
        shiftKey,
        cancelable: true,
      });
      assert.equal(canvas.dispatchEvent(event), false, key);
      assert.equal(event.defaultPrevented, true);
    }
  const unrelated = new dom.window.KeyboardEvent("keydown", {
    key: "Tab",
    cancelable: true,
  });
  assert.equal(canvas.dispatchEvent(unrelated), true);
  engine.focusPoint(engine.points[0]);
  canvas.dispatchEvent(
    new dom.window.KeyboardEvent("keydown", { key: "Enter", cancelable: true }),
  );
  assert.equal(selected[0], engine.points[0].row);
});
test("actual wheel and pointer dispatch distinguish hover, drag, cancellation and a fresh deliberate click", (context) => {
  /** @type {import("../../application-data.js").ApplicationFacility[]} */
  const selected = [];
  const { engine, canvas, rows, dom } = mount(context, {
    /**
     * Retain the actual original row emitted by native activation.
     * @param {import("../../application-data.js").ApplicationFacility} row Original selected source row.
     * @returns {number} Number of retained original emissions.
     */
    onSelect: (row) => selected.push(row),
  });
  const row = rows.find((row) => row.lat !== null && row.lon !== null);
  assert.ok(row);
  engine.setData([row]);
  engine.viewport.centreOn(engine.points[0].x, engine.points[0].y, 8);
  engine.draw();
  const point = engine.viewport.toScreen(
      engine.points[0].x,
      engine.points[0].y,
    ),
    position = { clientX: point.x, clientY: point.y, pointerId: 1 };
  canvas.dispatchEvent(new dom.window.PointerEvent("pointermove", position));
  assert.equal(engine.focus?.row, row);
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerdown", position));
  canvas.dispatchEvent(
    new dom.window.PointerEvent("pointermove", {
      ...position,
      clientX: point.x + 40,
    }),
  );
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerup", position));
  canvas.dispatchEvent(new dom.window.MouseEvent("click", position));
  assert.equal(selected.length, 0);
  canvas.dispatchEvent(new dom.window.PointerEvent("pointerdown", position));
  canvas.dispatchEvent(new dom.window.PointerEvent("pointercancel", position));
  canvas.dispatchEvent(new dom.window.MouseEvent("click", position));
  assert.equal(selected.length, 0);
  engine.viewport.centreOn(engine.points[0].x, engine.points[0].y, 8);
  engine.draw();
  canvas.dispatchEvent(new dom.window.MouseEvent("click", position));
  assert.equal(selected[0], row);
  const wheel = new dom.window.WheelEvent("wheel", {
    clientX: point.x,
    clientY: point.y,
    deltaY: -100,
    cancelable: true,
  });
  const zoom = engine.viewport.zoom;
  assert.equal(canvas.dispatchEvent(wheel), false);
  assert.ok(engine.viewport.zoom > zoom);
});
test("same actual classic interaction API is loaded in a real DOM Window", (context) => {
  const { dom } = mount(context);
  classic(dom);
  const result = /** @type {unknown} */ (
    vm.runInContext(
      "typeof AtlasMap.interactions.handleKey",
      dom.getInternalVMContext(),
    )
  );
  assert.equal(result, "function");
});
