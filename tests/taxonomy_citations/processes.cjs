// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — processes citation contracts.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const {
  readCitations,
} = require("../../04_interactive_presentation/scripts/taxonomy_citations.cjs");
const {
  loadFixture,
  findRequired,
  getRequired,
  physicalField,
} = require("../taxonomy_citation_fixture.cjs");
const root = path.resolve(__dirname, "../..");
const { rows, original } = loadFixture(root);

test("chemical entries retain operating modes and resolve model, exothermic and staged-process boundaries", () => {
  const resolved = readCitations(root, rows);
  /** @type {Record<string, [string, number]>} */
  const expected = {
    "batch-reactor": ["operating mode", 4],
    "semi-batch-reactor": ["operating mode", 4],
    "continuous-stirred-tank-reactor-cstr": ["architecture", 6],
    "plug-flow-tubular-reactor": ["architecture", 5],
    "cstr-cascade": ["configuration", 6],
  };
  for (const [id, [kind, count]] of Object.entries(expected)) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id);
    assert.equal(row.kind, kind);
    assert.equal(row.maturity, "deployed");
    assert.equal(row.evidence, "established");
    assert.equal(claims.length, count);
    assert.deepEqual(
      [...new Set(claims.map((claim) => claim.topic))],
      ["principle", "strength", "challenge"],
    );
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.equal(claim.source_capture_method, "publisher-tls");
      assert.ok(claim.source_captured_at !== null);
      assert.match(claim.source_captured_at, /^2026-10-01T/);
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  const batch = getRequired(resolved, "batch-reactor");
  assert.deepEqual(batch[0].pdf_pages, [1, 2]);
  assert.deepEqual(batch[0].printed_pages, ["unnumbered first page", "2"]);
  assert.match(
    findRequired(rows, (row) => row.id === "batch-reactor").challenge,
    /exothermic/,
  );
  const semi = findRequired(
    getRequired(resolved, "semi-batch-reactor"),
    (claim) => claim.topic === "challenge",
  );
  assert.deepEqual(semi.pdf_pages, [24, 27, 28, 35]);
  assert.match(semi.scope, /does not completely stop reaction/);
  assert.match(
    findRequired(
      rows,
      (row) => row.id === "continuous-stirred-tank-reactor-cstr",
    ).principle,
    /ideal well-mixed model/,
  );
  assert.match(
    findRequired(rows, (row) => row.id === "plug-flow-tubular-reactor")
      .principle,
    /ideal plug-flow model/,
  );
  const cascade = getRequired(resolved, "cstr-cascade");
  assert.equal(
    findRequired(rows, (row) => row.id === "cstr-cascade").parent_id,
    "continuous-stirred-tank-reactor-cstr",
  );
  assert.match(
    findRequired(cascade, (claim) => claim.source_id === "squ-step-feed").scope,
    /no advantage over a single reactor/,
  );
  assert.match(
    findRequired(
      cascade,
      (claim) => claim.source_id === "ima-reactive-crystallisation",
    ).scope,
    /burst interstage pumping/,
  );
  assert.match(
    findRequired(
      cascade,
      (claim) => claim.source_id === "uow-two-cstr-abstract",
    ).scope,
    /two physical CSTRs/,
  );
  assert.deepEqual(
    findRequired(cascade, (claim) => claim.source_id === "buffalo-networks")
      .pdf_pages,
    [2, 3, 4],
  );
});

test("electrochemical field sources retain reaction, page and energy-accounting boundaries", () => {
  const result = readCitations(root, rows);
  const ids = [
    "alkaline-water-electrolyser",
    "pem-water-electrolyser",
    "solid-oxide-electrolyser",
    "anion-exchange-membrane-electrolyser",
    "pem-fuel-cell",
    "alkaline-fuel-cell",
    "phosphoric-acid-fuel-cell",
    "molten-carbonate-fuel-cell",
    "solid-oxide-fuel-cell",
  ];
  for (const id of ids) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(result, id).filter((claim) =>
      ["principle", "strength", "challenge"].includes(claim.topic),
    );
    assert.deepEqual(
      claims.map((claim) => claim.topic),
      ["principle", "strength", "challenge"],
    );
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.equal(claim.source_capture_method, "publisher-tls");
      assert.ok(claim.source_captured_at !== null);
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  const oxide = getRequired(result, "solid-oxide-electrolyser");
  const reaction = findRequired(oxide, (claim) => claim.topic === "principle");
  assert.deepEqual(reaction.pdf_pages, [6, 8]);
  assert.deepEqual(reaction.printed_pages, ["1", "3"]);
  assert.match(reaction.source_title, /H2O-CO2 Co-Electrolysis/);
  assert.match(
    findRequired(oxide, (claim) => claim.topic === "strength").scope,
    /does not remove the heat input/,
  );
  const pem = findRequired(
    getRequired(result, "pem-water-electrolyser"),
    (claim) => claim.topic === "principle",
  );
  assert.deepEqual(pem.pdf_pages, []);
  assert.match(pem.source_url, /hydrogen-production-electrolysis/);
  const alkaline = findRequired(
    getRequired(result, "alkaline-fuel-cell"),
    (claim) => claim.topic === "principle",
  );
  assert.deepEqual(alkaline.pdf_pages, [115]);
  assert.deepEqual(alkaline.printed_pages, ["4-3"]);
  const acid = findRequired(
    getRequired(result, "phosphoric-acid-fuel-cell"),
    (claim) => claim.topic === "challenge",
  );
  assert.deepEqual(acid.pdf_pages, [30, 134]);
  assert.deepEqual(acid.printed_pages, ["1-11", "5-5"]);
  assert.match(
    acid.scope,
    /not a demonstrated universal current stack lifetime/,
  );
  assert.match(
    findRequired(
      getRequired(result, "anion-exchange-membrane-electrolyser"),
      (claim) => claim.topic === "strength",
    ).scope,
    /not universal PGM-free commercial operation/,
  );
});

test("solar, plasma and bioelectrochemical citations retain their actual energy and source boundaries", () => {
  const resolved = readCitations(root, rows);
  const ids = [
    "solar-thermochemical-redox-reactor",
    "plasma-catalytic-reactor",
    "photovoltaic-photothermal-artificial-photosynthesis",
    "microbial-fuel-cell",
    "microbial-electrolysis-cell",
  ];
  for (const id of ids) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id);
    assert.equal(claims.length, 4);
    assert.equal(row.reviewed_on, "2026-09-26");
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
    for (const claim of claims.filter(
      (item) => item.topic !== "classification",
    )) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  assert.match(
    findRequired(getRequired(resolved, ids[0]), (c) => c.topic === "challenge")
      .scope,
    /local ceria cracking/,
  );
  assert.match(
    findRequired(getRequired(resolved, ids[1]), (c) => c.topic === "challenge")
      .scope,
    /Three GC injections/,
  );
  assert.equal(
    findRequired(rows, (r) => r.id === ids[2]).kind,
    "system integration",
  );
  assert.match(
    findRequired(getRequired(resolved, ids[2]), (c) => c.topic === "challenge")
      .scope,
    /allocated PV area/,
  );
  for (const id of ids.slice(3)) {
    for (const claim of getRequired(resolved, id)) {
      assert.deepEqual(claim.pdf_pages, []);
      assert.deepEqual(claim.printed_pages, []);
      assert.match(
        claim.source_url,
        /europepmc\/webservices\/rest\/PMC[0-9]+\/fullTextXML$/,
      );
      const source = findRequired(
        original.sources,
        (s) => s.id === claim.source_id,
      );
      assert.equal(source.format, "xml");
      assert.equal(source.page_count, 0);
    }
  }
  assert.equal(
    findRequired(rows, (r) => r.id === ids[4]).challenge,
    "Catalyst poisoning and full-system energy accounting",
  );
  assert.match(
    findRequired(getRequired(resolved, ids[4]), (c) => c.topic === "challenge")
      .scope,
    /substrate chemical energy/,
  );
});
