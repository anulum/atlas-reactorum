// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — repository_catalogue.test.cjs
"use strict";

const test = require("node:test"),
  assert = require("node:assert/strict");
const { actualPage, originalDocument } = require("./catalogue_dom_fixture.cjs");
require("../04_interactive_presentation/browser-elements.js");
require("../04_interactive_presentation/presentation-text.js");
require("../04_interactive_presentation/application-data.js");
const admission = globalThis.AtlasApplicationData;
require("../04_interactive_presentation/repository-catalogue-controller.js");
const api = globalThis.AtlasRepositoryCatalogue;
const rows = admission.repositories(originalDocument("anulum_reactor_repos"));
test("all30 retained repository cards preserve source order, dates, licenses and link boundaries", (context) => {
  const document = actualPage(context).window.document,
    before = JSON.stringify(rows);
  api.create(document, rows).start();
  const cards = [...document.querySelectorAll("#repoGrid .repo-card")];
  assert.equal(cards.length, 30);
  assert.deepEqual(
    cards.map((card) => card.querySelector("h4")?.textContent),
    rows.map((row) => row.name),
  );
  for (const [index, card] of cards.entries()) {
    assert.equal(card.getAttribute("target"), "_blank");
    assert.equal(card.getAttribute("rel"), "noopener");
    assert.ok(card.textContent?.includes(rows[index].updated_at.slice(0, 10)));
    assert.ok(card.textContent?.includes(rows[index].license));
  }
  assert.equal(JSON.stringify(rows), before);
});
test("real text events search metadata and no match removes old cards", (context) => {
  const dom = actualPage(context),
    document = dom.window.document;
  api.create(document, rows).start();
  const search = globalThis.AtlasBrowserElements.requireElement(
    document,
    "repoSearch",
    "input",
  );
  search.value = rows[0].name.toUpperCase();
  search.dispatchEvent(new dom.window.Event("input"));
  assert.ok(
    document.querySelector("#repoGrid")?.textContent?.includes(rows[0].name),
  );
  search.value = "no original repository has this exact full phrase";
  search.dispatchEvent(new dom.window.Event("input"));
  assert.equal(document.querySelectorAll("#repoGrid .repo-card").length, 0);
  assert.equal(
    document.querySelector("#repoGrid")?.textContent,
    "No matching reactor-system repositories.",
  );
});
test("absent catalogue remains empty and missing native controls refuse", (context) => {
  const document = actualPage(context).window.document;
  api.create(document, []).start();
  assert.equal(document.querySelectorAll("#repoGrid .repo-card").length, 0);
  document.getElementById("repoSearch")?.remove();
  assert.throws(() => api.create(document, rows).start(), /Required Atlas/);
});
