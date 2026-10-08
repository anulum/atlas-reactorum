// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original display panels, escaping and fallback source custody.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
require("../04_interactive_presentation/browser-elements.js");
require("../04_interactive_presentation/fallback-taxonomy.js");
require("../04_interactive_presentation/presentation-text.js");
require("../04_interactive_presentation/explanatory-panels.js");

/**
 * Own the actual maintained template as a native DOM until the case completes.
 * @param {import("node:test").TestContext} context Actual registered case lifetime.
 * @returns {Document} Actual parsed complete maintained presentation template.
 */
function actualPage(context) {
  const dom = new JSDOM(
    fs.readFileSync(
      path.join(__dirname, "../04_interactive_presentation/index.html"),
      "utf8",
    ),
  );
  context.after(() => dom.window.close());
  return dom.window.document;
}

test("authored fallback retains all31 display rows without inventing source identity or review", () => {
  const rows = globalThis.AtlasFallbackTaxonomy;
  assert.equal(rows.length, 31);
  assert.equal(rows[0].name, "PWR");
  assert.equal(rows[rows.length - 1].name, "LENR / cold fusion");
  for (const row of rows) {
    assert.equal(Object.keys(row).length, 12);
    assert.equal(Object.hasOwn(row, "id"), false);
    assert.equal(Object.hasOwn(row, "source_urls"), false);
    assert.equal(Object.hasOwn(row, "reviewed_on"), false);
  }
});

for (const topic of ["magnetic", "inertial", "magneto", "alternative"]) {
  test(`actual authored fusion panel renders its complete title and example list: ${topic}`, (context) => {
    const document = actualPage(context);
    globalThis.AtlasExplanatoryPanels.renderFusion(document, topic);
    const panel = globalThis.AtlasBrowserElements.requireElement(
      document,
      "fusionDetail",
      "div",
    );
    assert.ok(panel.querySelector("h3")?.textContent);
    assert.equal(panel.querySelectorAll("li").length, 6);
  });
}
for (const flow of ["batch", "cstr", "pfr", "bio"]) {
  test(`actual authored flow panel renders its diagram and all original context dimensions: ${flow}`, (context) => {
    const document = actualPage(context);
    globalThis.AtlasExplanatoryPanels.renderFlow(document, flow);
    const panel = globalThis.AtlasBrowserElements.requireElement(
      document,
      "flowDemo",
      "div",
    );
    assert.equal(panel.querySelectorAll("dt").length, 3);
    assert.ok(panel.querySelector(flow === "pfr" ? ".tube" : ".vessel"));
  });
}

test("missing, unknown and prototype identities cannot render invented explanations", (context) => {
  const document = actualPage(context);
  const panels = globalThis.AtlasExplanatoryPanels;
  panels.renderFusion(document, "magnetic");
  panels.renderFlow(document, "batch");
  const before = [
    document.getElementById("fusionDetail")?.innerHTML,
    document.getElementById("flowDemo")?.innerHTML,
  ];
  for (const value of [undefined, "unavailable", "toString", "__proto__"]) {
    assert.throws(
      () => panels.renderFusion(document, value),
      /Authored fusion topic is unavailable/,
    );
    assert.throws(
      () => panels.renderFlow(document, value),
      /Authored flow is unavailable/,
    );
  }
  assert.deepEqual(
    [
      document.getElementById("fusionDetail")?.innerHTML,
      document.getElementById("flowDemo")?.innerHTML,
    ],
    before,
  );
});

test("original text representation, source order, duplicate handling and URL policy remain explicit", () => {
  const api = globalThis.AtlasPresentationText;
  assert.equal(
    api.escape('<tag "x">&\''),
    "&lt;tag &quot;x&quot;&gt;&amp;&#39;",
  );
  assert.equal(api.escape(null), "null");
  assert.equal(api.escape(undefined), "undefined");
  assert.equal(
    api.safeUrl("https://example.org/?x=a&y=b"),
    "https://example.org/?x=a&amp;y=b",
  );
  assert.equal(api.safeUrl("http://example.org/"), "http://example.org/");
  for (const value of [
    undefined,
    "invalid",
    "file:///example",
    "javascript:void(0)",
  ])
    assert.equal(api.safeUrl(value), "#");
  assert.equal(api.sourceLinks(undefined), "");
  assert.equal(api.sourceLinks([null, undefined, ""]), "");
  const first = "https://example.org/one";
  const second = { url: "https://example.org/two", title: "Second & source" };
  const rendered = api.sourceLinks([
    first,
    first,
    second,
    { url: "https://example.org/three" },
  ]);
  assert.equal((rendered.match(/<a /g) || []).length, 3);
  assert.ok(rendered.indexOf(first) < rendered.indexOf(second.url));
  assert.ok(rendered.includes("Second &amp; source"));
  assert.ok(rendered.includes(">https://example.org/three ↗</a>"));
});
