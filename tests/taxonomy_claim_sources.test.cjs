// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — taxonomy detail citation presentation conformance
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { readCitations } = require("../04_interactive_presentation/scripts/taxonomy_citations.cjs");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
global.window = {};
require("../04_interactive_presentation/data/taxonomy-expanded.js");
const citations = readCitations(path.resolve(__dirname, ".."), window.REACTOR_TAXONOMY);
const { render } = globalThis.AtlasTaxonomyCitations;

test("render every source-inspected statement and retain each exact scope and source-copy date boundary", () => {
  const allClaims = [...citations.values()].flat();
  const parsed = spawnSync("python3", ["-c", `
import json, sys
from html.parser import HTMLParser
class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, value):
        self.parts.append(value)
result = []
for markup in json.load(sys.stdin):
    parser = Text()
    parser.feed(markup)
    parser.close()
    result.append("".join(parser.parts))
json.dump(result, sys.stdout)
`], { input: JSON.stringify(allClaims.map(claim => render([claim]))), encoding: "utf8", timeout: 15000 });
  assert.equal(parsed.status, 0, parsed.stderr);
  const textById = new Map(allClaims.map((claim, index) => [claim.id, JSON.parse(parsed.stdout)[index]]));
  for (const claims of citations.values()) {
    const html = render(claims);
    assert.match(html, /Full review of this entry remains pending/);
    assert.equal((html.match(/<li>/g) || []).length, claims.length);
    if (claims.length === 0) assert.match(html, /No claim-level citation/);
    for (const claim of claims) {
      const statementHtml = render([claim]);
      assert.ok(textById.get(claim.id).includes(claim.statement));
      assert.ok(textById.get(claim.id).includes(claim.scope));
      assert.ok(statementHtml.includes(claim.reviewed_on));
      assert.match(statementHtml, /rel="noopener noreferrer"/);
      if (claim.source_capture_method === "retained-source-review") {
        assert.match(statementHtml, /Retained source copy; original retrieval date unknown/);
        assert.ok(!statementHtml.includes("Source copy retrieved:"));
      } else {
        assert.ok(statementHtml.includes(`Source copy retrieved: ${claim.source_captured_at.slice(0, 10)}`));
        assert.ok(!statementHtml.includes("original retrieval date unknown"));
      }
      if (claim.pdf_pages.length) {
        assert.ok(statementHtml.includes(`#page=${claim.pdf_pages[0]}`));
        assert.ok(statementHtml.includes(`printed page(s) ${claim.printed_pages.join(", ")}`));
        assert.ok(statementHtml.includes(`PDF page(s) ${claim.pdf_pages.join(", ")} (one-based)`));
      } else {
        assert.ok(statementHtml.includes(`href="${claim.source_url}"`));
        assert.ok(!statementHtml.includes("PDF page(s)"));
      }
    }
  }
});

test("preserve an existing PDF fragment and render citation typography as text", () => {
  const claim = structuredClone(citations.get("pwr")[0]);
  claim.source_url += "#page=11";
  claim.statement += ' & < > " \' ';
  claim.scope += " & explanation";
  const html = render([claim]);
  assert.equal((html.match(/#page=/g) || []).length, 1);
  assert.match(html, /&amp; &lt; &gt; &quot; &#39;/);
  assert.match(html, /&amp; explanation/);
});

test("refuse a non-HTTPS source rather than rendering a misleading source link", () => {
  const claim = structuredClone(citations.get("pwr")[0]);
  claim.source_url = claim.source_url.replace("https:", "http:");
  assert.throws(() => render([claim]), /anonymous HTTPS/);
});

test("refuse an unsupported source-copy provenance instead of presenting a retrieval claim", () => {
  const claim = structuredClone(citations.get("pwr")[0]);
  claim.source_capture_method = "original-retrieval-verified-by-assumption";
  assert.throws(() => render([claim]), /unsupported capture method/);
});

test("render the actual XML beam-target source through its inspected sections without PDF links or pagination", () => {
  const claims = citations.get("electrochemically-loaded-beam-target-fusion");
  const html = render(claims);
  assert.equal((html.match(/<li>/g) || []).length, 4);
  assert.ok(html.includes('href="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12367529/fullTextXML"'));
  assert.match(html, /Electrochemically enhanced fusion \(Sec4\)/);
  assert.match(html, /Conclusion \(Sec5\)/);
  assert.match(html, /could not measure the D\/Pd ratio directly/);
  assert.match(html, /Full review of this entry remains pending/);
  assert.ok(!html.includes("#page="));
  assert.ok(!html.includes("PDF page(s)"));
  assert.ok(!html.includes("printed page(s)"));
});

test("actual contested source details retain unknown dates, null tests and prospective demonstration boundaries", () => {
  const gas = render(citations.get("gas-loaded-metal-hydrogen-lenr"));
  assert.match(gas, /belief rather than a proven fact/);
  assert.match(gas, /omitted report sections/);
  const cave = render(citations.get("cavitation-bubble-fusion"));
  assert.equal((cave.match(/<li>/g) || []).length, 5);
  assert.match(cave, /prospective success criteria/);
  assert.match(cave, /No tritium measurement/);
  assert.ok(cave.includes("https://arxiv.org/abs/1209.2407#page=11"));
  assert.ok(cave.includes("https://doi.org/10.1103/PhysRevLett.89.104302#page=1"));
  const pd = render(citations.get("palladium-deuterium-electrochemical-lenr"));
  assert.match(pd, /Internet edition 4 of 5/);
  assert.match(pd, /Unknown|unknown/);
});

test("actual propulsion details show historical qualification limits and distinguish projected power from heating observations", () => {
  const rocket = render(citations.get("solid-core-nuclear-thermal-rocket"));
  assert.match(rocket, /not completed flight qualification/);
  assert.ok(rocket.includes("https://ntrs.nasa.gov/api/citations/19920005899/downloads/19920005899.pdf#page=9"));
  const fragments = render(citations.get("fission-fragment-propulsion-reactor"));
  assert.match(fragments, /modeled designs, not a built engine/);
  const antimatter = render(citations.get("antiproton-catalysed-microfission-fusion"));
  assert.match(antimatter, /positive hydrogen ions, not stored antiprotons/);
  const direct = render(citations.get("direct-fusion-drive"));
  assert.equal((direct.match(/<li>/g) || []).length, 4);
  assert.match(direct, /projected design budgets, not measured/);
  assert.match(direct, /historical report/);
  assert.ok(direct.includes("https://ntrs.nasa.gov/api/citations/20190031807/downloads/20190031807.pdf#page=12"));
});

test("actual energy-system details preserve allocated-area and XML locator boundaries", () => {
  const solar = render(citations.get("solar-thermochemical-redox-reactor"));
  assert.match(solar, /local ceria cracking/);
  const plasma = render(citations.get("plasma-catalytic-reactor"));
  assert.match(plasma, /cross-laboratory reproducibility/);
  const photosynthesis = render(citations.get("photovoltaic-photothermal-artificial-photosynthesis"));
  assert.match(photosynthesis, /allocated PV area/);
  assert.ok(photosynthesis.includes("https://arxiv.org/pdf/2204.04971v1#page=7"));
  for (const id of ["microbial-fuel-cell", "microbial-electrolysis-cell"]) {
    const html = render(citations.get(id));
    assert.equal((html.match(/<li>/g) || []).length, 4);
    assert.match(html, /fullTextXML/);
    assert.ok(!html.includes("#page="));
    assert.match(html, /Full review of this entry remains pending/);
  }
  assert.match(render(citations.get("microbial-electrolysis-cell")), /substrate chemical energy/);
});
