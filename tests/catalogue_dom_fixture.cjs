// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — catalogue_dom_fixture.cjs
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { JSDOM } = require("jsdom");
const root = path.resolve(__dirname, "..");
/**
 * Own the complete actual maintained template as a real parsed DOM.
 * @param {import("node:test").TestContext} context Registered native test lifetime.
 * @returns {import("jsdom").JSDOM} Actual template/document/window, closed after the case.
 */
function actualPage(context) {
  const dom = new JSDOM(
    fs.readFileSync(
      path.join(root, "04_interactive_presentation/index.html"),
      "utf8",
    ),
    { runScripts: "outside-only" },
  );
  context.after(() => dom.window.close());
  return dom;
}
/**
 * Read one complete retained generated document without typing unchecked JSON.
 * @param {string} name Actual generated document basename.
 * @returns {unknown} Original decoded source cells, before owning admission.
 */
function originalDocument(name) {
  return /** @type {unknown} */ (
    JSON.parse(
      fs.readFileSync(
        path.join(root, "04_interactive_presentation/data", name + ".json"),
        "utf8",
      ),
    )
  );
}
/**
 * Execute the actual unchanged classic-script source in its real DOM Window.
 * @param {import("jsdom").JSDOM} dom Actual template Window owned by the test.
 * @param {string[]} names Production script paths relative to the presentation directory.
 * @returns {void} Actual loaded namespaces; no replacement Window or DOM method.
 */
function loadScripts(dom, names) {
  for (const name of names) {
    const filename = path.join(root, "04_interactive_presentation", name);
    vm.runInContext(
      fs.readFileSync(filename, "utf8"),
      dom.getInternalVMContext(),
      { filename },
    );
  }
}
module.exports = { actualPage, originalDocument, loadScripts };
