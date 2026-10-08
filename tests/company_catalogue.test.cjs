// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — company_catalogue.test.cjs
"use strict";

const test = require("node:test"),
  assert = require("node:assert/strict");
const { actualPage, originalDocument } = require("./catalogue_dom_fixture.cjs");
require("../04_interactive_presentation/browser-elements.js");
require("../04_interactive_presentation/presentation-text.js");
require("../04_interactive_presentation/application-data.js");
const admission = globalThis.AtlasApplicationData;
require("../04_interactive_presentation/company-catalogue-controller.js");
const api = globalThis.AtlasCompanyCatalogue;
const rows = admission.companies(originalDocument("fusion_companies.sample"));
const elements = globalThis.AtlasBrowserElements;
/**
 * Dispatch the original native form event after selecting an actual source value.
 * @param {Document} document Actual maintained template.
 * @param {string} id Original company control identity.
 * @param {string} value Actual source facet/text value.
 * @returns {void} The real bound handler renders the new selection.
 */
function choose(document, id, value) {
  const control = elements.requireElement(
    document,
    id,
    id === "companySearch" ? "input" : "select",
  );
  control.value = value;
  const window = document.defaultView;
  assert.ok(window);
  control.dispatchEvent(
    new window.Event(id === "companySearch" ? "input" : "change"),
  );
}
test("all98 original cards retain company claims, independent milestones and source order", (context) => {
  const document = actualPage(context).window.document,
    before = JSON.stringify(rows);
  api.create(document, rows).start();
  const cards = [...document.querySelectorAll("#companyGrid article")];
  assert.equal(cards.length, 98);
  assert.deepEqual(
    cards.map((card) => card.querySelector("h3")?.textContent),
    rows.map((row) => row.name),
  );
  for (const [index, card] of cards.entries()) {
    assert.ok(
      card.textContent?.includes(rows[index].company_claim || "Not catalogued"),
    );
    assert.ok(
      card.textContent?.includes(
        rows[index].independent_evidence || "Not assessed",
      ),
    );
  }
  assert.equal(JSON.stringify(rows), before);
});
test("every real facet and text event filters original identities and an empty search clears cards", (context) => {
  const document = actualPage(context).window.document;
  api.create(document, rows).start();
  for (const [id, field] of [
    ["companyApproach", "approach"],
    ["companyCountry", "country"],
    ["companyEvidence", "evidence"],
    ["companyStatus", "status"],
  ]) {
    const value = String(rows[0][field]);
    choose(document, id, value);
    const expected = rows
      .filter((row) => row[field] === value)
      .map((row) => row.name);
    assert.deepEqual(
      [...document.querySelectorAll("#companyGrid h3")].map(
        (node) => node.textContent,
      ),
      expected,
    );
    choose(document, id, "all");
  }
  choose(document, "companySearch", rows[0].name.toUpperCase());
  assert.ok(
    document.querySelector("#companyGrid")?.textContent?.includes(rows[0].name),
  );
  choose(
    document,
    "companySearch",
    "no original company has this exact full phrase",
  );
  assert.equal(document.querySelectorAll("#companyGrid article").length, 0);
  assert.equal(
    document.querySelector("#companyGrid")?.textContent,
    "No matching companies.",
  );
  assert.equal(
    document.querySelector("#companyCount")?.textContent,
    "0 of 98 audited company/project records",
  );
});
test("source absence and optional producer cells remain absent and text stays escaped", (context) => {
  const document = actualPage(context).window.document;
  /** @type {import("../04_interactive_presentation/application-data.js").ApplicationCompany} */
  const changed = {
    ...rows[0],
    company_claim: "",
    independent_evidence: "",
    source_urls: undefined,
    name: rows[0].name + " <script>owned source control</script>",
  };
  for (const field of [
    "identity_class",
    "public_devices_projects",
    "evidence_tier",
    "status_detail",
    "confidence",
    "data_caveat",
    "evidence_maturity",
    "notes",
  ])
    delete changed[field];
  const admitted = admission.companies([changed]);
  api.create(document, admitted).start();
  assert.equal(document.querySelectorAll("#companyGrid script").length, 0);
  assert.ok(
    document.querySelector("#companyGrid")?.textContent?.includes(changed.name),
  );
  assert.ok(
    document
      .querySelector("#companyGrid")
      ?.textContent?.includes("Not assessed"),
  );
  const empty = actualPage(context).window.document;
  api.create(empty, []).start();
  assert.equal(
    empty.querySelector("#companyCount")?.textContent,
    "0 of 0 audited company/project records",
  );
});
test("wrong or missing actual company controls refuse through the owning entry point", (context) => {
  const document = actualPage(context).window.document;
  document.getElementById("companyApproach")?.remove();
  assert.throws(() => api.create(document, rows).start(), /Required Atlas/);
});

test("explicit absent company facets do not become blank selectable categories", (context) => {
  const document = actualPage(context).window.document;
  const absent = admission.companies([
    { ...rows[0], approach: "", country: "", evidence: "", status: "" },
  ]);
  api.create(document, absent).start();
  for (const id of [
    "companyApproach",
    "companyCountry",
    "companyEvidence",
    "companyStatus",
  ]) {
    const control = elements.requireElement(document, id, "select");
    assert.equal(control.options.length, 1);
    assert.equal(control.options[0].value, "all");
  }
  assert.equal(document.querySelectorAll("#companyGrid article").length, 1);
});

test("optional producer registry notes retain their supplied source text", (context) => {
  const document = actualPage(context).window.document;
  const note = rows[0].independent_evidence;
  assert.ok(note.length > 0);
  const supplied = admission.companies([{ ...rows[0], notes: note }]);
  api.create(document, supplied).start();
  const card = document.querySelector("#companyGrid article");
  assert.ok(card);
  const key = [...card.querySelectorAll("dt")].find(
    (node) => node.textContent === "Registry notes",
  );
  assert.equal(key?.nextElementSibling?.textContent, note);
  assert.equal(supplied[0].notes, note);
});
