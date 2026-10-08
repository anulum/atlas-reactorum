// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native browser fixture for map engine gestures.

/**
 * Original-row selection and starting viewport retained for gesture observations.
 * @typedef {{container:HTMLElement,engine:InstanceType<typeof import("../engine.js")>,selected:import("../engine.js").FacilityRow[],centre:number}} GestureState
 */
/**
 * Methods invoked by the owning Python test through the real Chrome runtime.
 * @typedef {{setup:()=>{x:number,y:number,zoom:number},afterDrag:()=>Promise<{zoom:number,panned:boolean,selected:number}>,glyph:()=>{x:number,y:number},afterClick:()=>Promise<{zoom:number,selected:number}>,capture:(pointerId:number)=>boolean,cleanup:()=>void}} GestureAPI
 */

/**
 * Install the fixture into the already loaded canonical Atlas page.
 * @returns {void}
 */
(function () {
  "use strict";
  /** @type {Window & import("../engine.js").EngineGlobal & {REACTOR_FACILITIES?:unknown,__engineGestureTests?:GestureAPI}} */
  const root = window;
  /** @type {GestureState|null} */
  let current = null;

  /**
   * Retrieve the mounted fixture after setup.
   * @returns {GestureState} Actual native DOM map and original source selections.
   * @throws {Error} If the owning test has not mounted its fixture.
   */
  function state() {
    if (!current) throw new Error("Map gesture fixture is not mounted");
    return current;
  }

  /**
   * Mount a real canvas around an unchanged co-located pair from the shipped source.
   * @returns {{x:number,y:number,zoom:number}} Native client position of the aggregate glyph.
   * @throws {Error} If the canonical page lacks source rows, its constructor or a co-located pair.
   */
  function setup() {
    const Engine = root.AtlasMap && root.AtlasMap.MapEngine;
    const input = root.REACTOR_FACILITIES;
    if (!Engine || !input)
      throw new Error("Canonical Atlas map and rows are required");
    const rows = globalThis.AtlasApplicationData.facilities(input);
    /** @type {Map<string,import("../engine.js").FacilityRow>} */
    const groups = new Map();
    /** @type {import("../engine.js").FacilityRow[]|null} */
    let pair = null;
    for (const row of rows) {
      if (typeof row.lon !== "number" || typeof row.lat !== "number") continue;
      const key = row.lon + ":" + row.lat;
      const previous = groups.get(key);
      if (previous) {
        pair = [previous, row];
        break;
      }
      groups.set(key, row);
    }
    if (!pair) throw new Error("No original co-located source pair");
    const container = document.createElement("div");
    container.style.cssText =
      "position:fixed;left:20px;top:20px;width:600px;height:300px;z-index:1000000";
    document.body.appendChild(container);
    /** @type {import("../engine.js").FacilityRow[]} */
    const selected = [];
    const engine = new Engine({
      container,
      /**
       * Retain actual original-row emissions without cloning the source.
       * @param {import("../engine.js").FacilityRow} row Selected original row.
       * @returns {void}
       */
      onSelect: (row) => {
        selected.push(row);
      },
    });
    engine.resize();
    engine.setData(pair);
    const point = engine.points[0];
    engine.viewport.centreOn(point.x, point.y, 4);
    engine.draw();
    current = { container, engine, selected, centre: engine.viewport.centreX };
    return { ...glyph(), zoom: engine.viewport.zoom };
  }

  /**
   * Observe the drag only after the engine's actual scheduled paint.
   * @returns {Promise<{zoom:number,panned:boolean,selected:number}>} Current viewport and source emission observation.
   */
  async function afterDrag() {
    await new Promise(requestAnimationFrame);
    const value = state();
    return {
      zoom: value.engine.viewport.zoom,
      panned: value.engine.viewport.centreX !== value.centre,
      selected: value.selected.length,
    };
  }

  /**
   * Locate the actual count-two canvas glyph in client coordinates after its latest paint.
   * @returns {{x:number,y:number}} Native click target, including the real canvas offset.
   * @throws {Error} If the source pair is no longer represented by its aggregate glyph.
   */
  function glyph() {
    const value = state();
    const entry = value.engine.clusters.find(
      /**
       * Select the glyph representing the unchanged two source records.
       * @param {import("../cluster.js").ClusterEntry<import("../engine.js").FacilityPoint<import("../engine.js").FacilityRow>>} candidate Drawn glyph.
       * @returns {boolean} Whether exactly the two fixture rows are represented.
       */
      (candidate) => candidate.count === 2,
    );
    if (!entry)
      throw new Error("Original pair did not form its expected glyph");
    const rect = value.engine.canvas.getBoundingClientRect();
    return { x: rect.left + entry.x, y: rect.top + entry.y };
  }

  /**
   * Observe deliberate click activation after the real scheduled paint.
   * @returns {Promise<{zoom:number,selected:number}>} Current zoom and original-row emission count.
   */
  async function afterClick() {
    await new Promise(requestAnimationFrame);
    const value = state();
    return {
      zoom: value.engine.viewport.zoom,
      selected: value.selected.length,
    };
  }

  /**
   * Remove only this fixture's native DOM container and retained source references.
   * @returns {void}
   */
  function cleanup() {
    if (current) current.container.remove();
    current = null;
  }

  /**
   * Read native pointer capture on the actual mounted canvas.
   * @param {number} pointerId Browser pointer identifier.
   * @returns {boolean} Whether Chrome retains capture for that pointer.
   * @throws {Error} If the fixture canvas is absent.
   */
  function capture(pointerId) {
    const canvas = state().container.querySelector("canvas");
    if (!canvas) throw new Error("Fixture canvas is absent");
    return canvas.hasPointerCapture(pointerId);
  }

  root.__engineGestureTests = {
    setup,
    afterDrag,
    glyph,
    afterClick,
    capture,
    cleanup,
  };
})();
