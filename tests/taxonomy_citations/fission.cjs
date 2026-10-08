// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — fission citation contracts.
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

test("heavy-water and graphite claims resolve complete fields, irregular scanned pages and bounded historical evidence", () => {
  const resolved = readCitations(root, rows);
  const expected = {
    "phwr-candu": [
      [11, 26],
      [26, 31],
      [127, 128, 156, 157],
    ],
    "heavy-water-pressure-vessel-reactor": [
      [87, 88, 90, 91],
      [11, 88, 102],
      [95, 102, 156, 157],
    ],
    "magnox-gas-cooled-reactor": [[197], [73], [74, 75, 84, 201]],
    "advanced-gas-cooled-reactor-agr": [[], [], []],
    "rbmk-pressure-tube-reactor": [[113], [18], [13, 14, 138]],
  };
  for (const [id, pages] of Object.entries(expected)) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id).filter((claim) =>
      ["principle", "strength", "challenge"].includes(claim.topic),
    );
    assert.deepEqual(
      claims.map((claim) => claim.topic),
      ["principle", "strength", "challenge"],
    );
    assert.deepEqual(
      claims.map((claim) => claim.pdf_pages),
      pages,
    );
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.ok(claim.section.length && claim.scope.length);
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  const magnox = getRequired(resolved, "magnox-gas-cooled-reactor").filter(
    (claim) => claim.topic !== "classification",
  );
  assert.deepEqual(
    magnox.map((claim) => claim.printed_pages),
    [["204"], ["71"], ["72", "73", "82", "208"]],
  );
  assert.ok(
    magnox.every(
      (claim) =>
        claim.source_captured_at === null &&
        claim.source_capture_method === "retained-source-review",
    ),
  );
  const agr = getRequired(resolved, "advanced-gas-cooled-reactor-agr").filter(
    (claim) => claim.topic !== "classification",
  );
  assert.ok(
    agr.every(
      (claim) =>
        claim.source_capture_method === "publisher-tls" &&
        claim.source_captured_at !== null,
    ),
  );
  assert.match(
    findRequired(agr, (claim) => claim.topic === "challenge").scope,
    /Sizewell B/,
  );
  assert.match(
    findRequired(
      rows,
      (row) => row.id === "heavy-water-pressure-vessel-reactor",
    ).challenge,
    /fuel-channel materials degradation/,
  );
  assert.match(
    findRequired(
      getRequired(resolved, "rbmk-pressure-tube-reactor"),
      (claim) => claim.topic === "challenge",
    ).scope,
    /not universal present-day/,
  );
});

test("research configurations resolve field sources and retain geometry, criticality and named-facility boundaries", () => {
  const result = readCitations(root, rows);
  const ids = [
    "pool-type-research-reactor",
    "tank-type-research-reactor",
    "tank-in-pool-research-reactor",
    "aqueous-homogeneous-reactor",
    "critical-assembly",
    "subcritical-assembly",
    "pulsed-research-reactor",
  ];
  for (const id of ids) {
    const row = findRequired(rows, (item) => item.id === id);
    const physical = getRequired(result, id).filter((claim) =>
      ["principle", "strength", "challenge"].includes(claim.topic),
    );
    assert.deepEqual(
      physical.map((claim) => claim.topic),
      ["principle", "strength", "challenge"],
    );
    for (const claim of physical) {
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
  const tankPool = findRequired(
    getRequired(result, "tank-in-pool-research-reactor"),
    (claim) => claim.topic === "strength",
  );
  assert.match(tankPool.scope, /not an attribute of every tank-in-pool/);
  assert.deepEqual(tankPool.pdf_pages, [21]);
  assert.deepEqual(tankPool.printed_pages, ["21"]);
  const aqueous = findRequired(
    getRequired(result, "aqueous-homogeneous-reactor"),
    (claim) => claim.topic === "challenge",
  );
  assert.deepEqual(aqueous.pdf_pages, [12, 13, 14, 15]);
  assert.deepEqual(aqueous.printed_pages, ["5", "6", "7", "8"]);
  assert.match(
    findRequired(
      getRequired(result, "aqueous-homogeneous-reactor"),
      (claim) => claim.topic === "strength",
    ).scope,
    /Uniform gas, density or neutron distributions/,
  );
  const critical = findRequired(
    getRequired(result, "critical-assembly"),
    (claim) => claim.topic === "challenge",
  );
  assert.match(
    critical.source_url,
    /epfl\.ch\/labs\/lrs\/facilities\/crocus-reactor\//,
  );
  assert.match(critical.scope, /not legal verification/);
  assert.deepEqual(critical.pdf_pages, []);
  const subcritical = findRequired(
    getRequired(result, "subcritical-assembly"),
    (claim) => claim.topic === "challenge",
  );
  assert.match(subcritical.scope, /independently of source characteristics/);
  const pulse = findRequired(
    getRequired(result, "pulsed-research-reactor"),
    (claim) => claim.topic === "principle",
  );
  assert.match(pulse.source_url, /triga\.uni-mainz\.de\/betriebsmodus\//);
  assert.match(pulse.scope, /not universal pulse capability/);
});

test("all six HTGR and fast-reactor entries expose full-field locators without changing their maturity or approving deployment", () => {
  const result = readCitations(root, rows);
  const expected = {
    "prismatic-htgr": [[13], [13, 19, 25], [19, 135]],
    "pebble-bed-htgr": [
      [13, 140],
      [13, 140],
      [60, 64, 66],
    ],
    "sodium-fast-reactor": [
      [212, 219, 550],
      [15, 212, 221],
      [559, 757],
    ],
    "lead-fast-reactor": [[285], [285], [285, 286, 287]],
    "lead-bismuth-fast-reactor": [[285], [285, 286], [286, 287]],
    "gas-cooled-fast-reactor": [[342, 344, 363], [343], [342, 360]],
  };
  for (const [id, locators] of Object.entries(expected)) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(result, id);
    assert.deepEqual(
      claims.map((citation) => citation.topic),
      ["principle", "strength", "challenge"],
    );
    assert.deepEqual(
      claims.map((citation) => citation.pdf_pages),
      locators,
    );
    assert.ok(
      claims.every(
        (citation) =>
          citation.source_captured_at === null &&
          citation.source_capture_method === "retained-source-review",
      ),
    );
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.deepEqual(
        claim.printed_pages,
        claim.pdf_pages.map((page) =>
          String(page - (id.includes("htgr") ? 8 : 13)),
        ),
      );
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  assert.equal(
    findRequired(rows, (row) => row.id === "sodium-fast-reactor").principle,
    "Liquid sodium cools a fast-neutron core.",
  );
  assert.match(
    getRequired(result, "sodium-fast-reactor")[0].scope,
    /hydride shielding/,
  );
  assert.match(
    findRequired(rows, (row) => row.id === "gas-cooled-fast-reactor").principle,
    /designs target refractory fuel/,
  );
  assert.match(
    getRequired(result, "gas-cooled-fast-reactor")[0].scope,
    /conventional MOX and steel cladding/,
  );
  assert.match(
    findRequired(rows, (row) => row.id === "gas-cooled-fast-reactor").strength,
    /^Targeted /,
  );
});

test("GIF SCWR and VHTR resolve actual full fields with HTML headings and known retrieval dates while keeping design potential explicit", () => {
  const resolved = readCitations(root, rows);
  const expected = [
    ["supercritical-water-reactor", "gif-scwr"],
    ["very-high-temperature-reactor-vhtr", "gif-vhtr"],
  ];
  for (const [id, sourceId] of expected) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id);
    assert.deepEqual(
      claims.map((claim) => claim.topic),
      ["principle", "strength", "challenge"],
    );
    const source = findRequired(
      original.sources,
      (item) => item.id === sourceId,
    );
    assert.equal(source.format, "html");
    assert.equal(source.page_count, 0);
    assert.equal(source.capture_method, "publisher-tls");
    assert.ok(source.captured_at !== null);
    assert.match(source.captured_at, /^2026-10-01T/);
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.equal(claim.source_url, source.url);
      assert.ok(row.source_urls.includes(source.url));
      assert.equal(claim.source_sha256, source.sha256);
      assert.equal(claim.source_captured_at, source.captured_at);
      assert.deepEqual(claim.pdf_pages, []);
      assert.deepEqual(claim.printed_pages, []);
      assert.ok(claim.section.length > 0);
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
    assert.equal(row.maturity, "concept");
    assert.equal(row.evidence, "research");
  }
  assert.match(
    getRequired(resolved, "supercritical-water-reactor")[1].scope,
    /not measured SCWR plant output/,
  );
  assert.match(
    getRequired(resolved, "very-high-temperature-reactor-vhtr")[0].scope,
    /lower-temperature HTGR examples/,
  );
  assert.match(
    findRequired(rows, (row) => row.id === "very-high-temperature-reactor-vhtr")
      .strength,
    /^Potential /,
  );
  assert.match(
    getRequired(resolved, "very-high-temperature-reactor-vhtr")[2].scope,
    /does not establish lifetime/,
  );
});

test("salt entries distinguish liquid fuel from fluoride coolant with retained IAEA locators and pending complete review", () => {
  const resolved = readCitations(root, rows);
  const expected = {
    "thermal-liquid-fuel-molten-salt-reactor": [
      [54, 68],
      [23, 24],
      [29, 30, 31, 33, 34],
    ],
    "fast-liquid-fuel-molten-salt-reactor": [
      [60, 64, 75],
      [61, 65, 75, 76],
      [29, 32, 34, 60, 65, 76],
    ],
    "fluoride-salt-cooled-high-temperature-reactor": [
      [51, 52],
      [51, 52],
      [29, 34, 52],
    ],
  };
  for (const [id, pages] of Object.entries(expected)) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id).filter((claim) =>
      ["principle", "strength", "challenge"].includes(claim.topic),
    );
    assert.deepEqual(
      claims.map((claim) => claim.topic),
      ["principle", "strength", "challenge"],
    );
    assert.deepEqual(
      claims.map((claim) => claim.pdf_pages),
      pages,
    );
    for (const claim of claims) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.equal(claim.source_capture_method, "retained-source-review");
      assert.equal(claim.source_captured_at, null);
      assert.deepEqual(
        claim.printed_pages,
        claim.pdf_pages.map((page) => String(page - 10)),
      );
      assert.ok(row.source_urls.includes(claim.source_url));
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  const coolant = findRequired(
    getRequired(resolved, "fluoride-salt-cooled-high-temperature-reactor"),
    (claim) => claim.topic === "fuel-state-classification",
  );
  assert.equal(
    coolant.source_url,
    "https://www-pub.iaea.org/MTCD/Publications/PDF/TE_1696_web.pdf",
  );
  assert.deepEqual(coolant.pdf_pages, [28]);
  assert.deepEqual(coolant.printed_pages, ["16"]);
  assert.equal(coolant.source_captured_at, null);
  assert.match(
    findRequired(
      rows,
      (row) => row.id === "thermal-liquid-fuel-molten-salt-reactor",
    ).principle,
    /moderated thermal-neutron core/,
  );
  assert.match(
    getRequired(resolved, "thermal-liquid-fuel-molten-salt-reactor")[0].scope,
    /circulation is not universal/,
  );
  assert.match(
    findRequired(
      rows,
      (row) => row.id === "fast-liquid-fuel-molten-salt-reactor",
    ).strength,
    /^Potential /,
  );
  assert.match(
    getRequired(resolved, "fast-liquid-fuel-molten-salt-reactor")[2].scope,
    /not an attribute of every fast MSR/,
  );
  assert.match(
    findRequired(
      rows,
      (row) => row.id === "fluoride-salt-cooled-high-temperature-reactor",
    ).challenge,
    /decay-heat removal/,
  );
});
