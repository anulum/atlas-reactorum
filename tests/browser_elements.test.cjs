// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — required controls in the actual maintained browser template.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
require("../04_interactive_presentation/browser-elements.js");

test("public control reader binds actual template elements and refuses missing or wrong controls", () => {
  const dom = new JSDOM(
    fs.readFileSync(
      path.join(__dirname, "../04_interactive_presentation/index.html"),
      "utf8",
    ),
  );
  try {
    const document = dom.window.document;
    const api = globalThis.AtlasBrowserElements;
    const buttons = api.requireElements(document, ".nav-dot", "button");
    assert.deepEqual(buttons, [...document.querySelectorAll(".nav-dot")]);
    assert.ok(buttons.length > 1);
    assert.deepEqual(api.requireElements(document, ".missing", "button"), []);
    assert.throws(() => api.requireElements(document, "[", "button"), {
      name: "SyntaxError",
    });
    assert.throws(
      () => api.requireElements(document, ".dialog-close", "select"),
      /Required Atlas control/,
    );
    const entry = api.requireElement(document, "historyEntry", "select");
    assert.equal(entry, document.getElementById("historyEntry"));
    assert.ok(entry instanceof dom.window.HTMLSelectElement);
    assert.equal(
      api.requireElement(document, "historyShare", "a").localName,
      "a",
    );
    assert.equal(
      api.requireElement(document, "correctionForm", "form").localName,
      "form",
    );
    assert.equal(
      api.requireElement(document, "correctionFields", "fieldset").localName,
      "fieldset",
    );
    assert.throws(
      () => api.requireElement(document, "missing-control", "select"),
      /Required Atlas control is unavailable: missing-control/,
    );
    assert.throws(
      () => api.requireElement(document, "historyShare", "select"),
      /Required Atlas control is unavailable: historyShare/,
    );
    entry.remove();
    assert.throws(
      () => api.requireElement(document, "historyEntry", "select"),
      /Required Atlas control is unavailable: historyEntry/,
    );
    const dialogClose = api.requireSelector(
      document,
      "button.dialog-close",
      "button",
    );
    assert.ok(dialogClose instanceof dom.window.HTMLButtonElement);
    assert.throws(
      () => api.requireSelector(document, ".missing", "button"),
      /Required Atlas control/,
    );
    assert.throws(() => api.requireSelector(document, "[", "button"), {
      name: "SyntaxError",
    });
    assert.throws(
      () => api.requireSelector(document, ".dialog-close", "select"),
      /Required Atlas control/,
    );
    const foreign = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "select",
    );
    foreign.id = "historyEntry";
    document.body.append(foreign);
    foreign.classList.add("foreign-control");
    assert.throws(
      () => api.requireElements(document, ".foreign-control", "select"),
      /Required Atlas control/,
    );
    assert.throws(
      () => api.requireSelector(document, ".foreign-control", "select"),
      /Required Atlas control/,
    );
    assert.throws(
      () => api.requireElement(document, "historyEntry", "select"),
      /Required Atlas control is unavailable: historyEntry/,
    );
  } finally {
    dom.window.close();
  }
});
