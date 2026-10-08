// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual complete-template native map fixture.
"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  vm = require("node:vm");
const { JSDOM } = require("jsdom");
const MapEngine = require("../engine.js");
require("../../application-data.js");
const assets = path.resolve(__dirname, "../..");
const original = globalThis.AtlasApplicationData.facilities(
  JSON.parse(
    fs.readFileSync(
      path.join(assets, "data/global_reactors.sample.json"),
      "utf8",
    ),
  ),
);
/**
 * Mount the actual engine in the complete original template and native raster backend.
 * @param {import("node:test").TestContext} context Owning native test lifetime.
 * @param {import("../engine.js").EngineOptions<import("../../application-data.js").ApplicationFacility>} [options] Actual constructor options and original-row callbacks.
 * @returns {{dom:import("jsdom").JSDOM,engine:import("../../browser-contracts.js").AtlasFacilityMap,canvas:HTMLCanvasElement,rows:import("../../application-data.js").ApplicationFacility[]}} Actual native document/canvas, complete original records and their engine.
 */
function mount(context, options = {}) {
  const dom = new JSDOM(
    fs.readFileSync(path.join(assets, "index.html"), "utf8"),
    { runScripts: "outside-only" },
  );
  context.after(() => dom.window.close());
  const container = dom.window.document.getElementById("mapHost");
  if (!container) throw Error("actual map host is absent");
  const engine = new MapEngine({ ...options, container });
  const canvas = container.querySelector("canvas");
  if (!canvas || !canvas.getContext("2d"))
    throw Error("native raster canvas is absent");
  canvas.width = 960;
  canvas.height = 480;
  engine.viewport.resize(960, 480);
  return { dom, engine, canvas, rows: original };
}
/**
 * Load the actual full map namespace in a genuine DOM Window with original source filenames.
 * @param {import("jsdom").JSDOM} dom Actual owned complete template Window.
 * @param {string[]} [omit] Explicit missing real module names for refusal cases.
 * @returns {void} Actual map scripts are evaluated in original dependency order.
 */
function classic(dom, omit = []) {
  for (const name of [
    "projection",
    "coastline",
    "quadtree",
    "cluster",
    "viewport",
    "renderer",
    "interactions",
    "accessibility",
    "engine",
  ]) {
    if (omit.includes(name)) continue;
    const filename = path.join(assets, "map", name + ".js");
    vm.runInContext(
      fs.readFileSync(filename, "utf8"),
      dom.getInternalVMContext(),
      { filename },
    );
  }
}
module.exports = { mount, classic };
