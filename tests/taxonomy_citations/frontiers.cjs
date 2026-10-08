// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — frontiers citation contracts.
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

test("externally driven fusion fields retain observed-mechanism, loading and neutron-spectrum boundaries", () => {
  const result = readCitations(root, rows);
  for (const id of [
    "muon-catalysed-fusion",
    "lattice-confinement-fusion",
    "electrochemically-loaded-beam-target-fusion",
    "pyroelectric-fusion-source",
  ]) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(result, id);
    assert.deepEqual(
      [...new Set(claims.map((claim) => claim.topic))],
      ["classification", "principle", "strength", "challenge"],
    );
    for (const claim of claims.filter(
      (claim) => claim.topic !== "classification",
    )) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
    }
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
  }
  const muon = getRequired(result, "muon-catalysed-fusion");
  assert.equal(muon[0].source_title, "Muon Catalyzed Fusion");
  assert.deepEqual(
    findRequired(muon, (claim) => claim.topic === "challenge").printed_pages,
    ["218", "219"],
  );
  assert.match(
    findRequired(muon, (claim) => claim.topic === "challenge").scope,
    /historical/,
  );
  assert.match(
    findRequired(rows, (row) => row.id === "lattice-confinement-fusion")
      .challenge,
    /resolving higher-energy neutron sources/,
  );
  const xml = findRequired(
    original.sources,
    (source) => source.id === "beam-chen2025",
  );
  assert.equal(xml.format, "xml");
  assert.equal(xml.page_count, 0);
  assert.equal(
    xml.sha256,
    "418993afce3145dc14c2865da34c1f9abb91d660cd1eb29d0237fbdf10896352",
  );
  for (const claim of getRequired(
    result,
    "electrochemically-loaded-beam-target-fusion",
  )) {
    assert.deepEqual(claim.pdf_pages, []);
    assert.deepEqual(claim.printed_pages, []);
    assert.equal(claim.source_url, xml.url);
    assert.match(claim.section, /Sec[1-5]/);
  }
  assert.match(
    findRequired(
      getRequired(result, "electrochemically-loaded-beam-target-fusion"),
      (claim) => claim.topic === "strength",
    ).scope,
    /could not measure the D\/Pd ratio directly/,
  );
  assert.match(
    findRequired(
      getRequired(result, "pyroelectric-fusion-source"),
      (claim) => claim.topic === "challenge",
    ).scope,
    /externally supplied heating\/cooling/,
  );
});

test("contested nuclear fields expose named null tests and prospective criteria without accepting nuclear output", () => {
  const resolved = readCitations(root, rows);
  const counts = {
    "palladium-deuterium-electrochemical-lenr": 8,
    "gas-loaded-metal-hydrogen-lenr": 5,
    "cavitation-bubble-fusion": 5,
  };
  for (const [id, count] of Object.entries(counts)) {
    const row = findRequired(rows, (item) => item.id === id);
    const claims = getRequired(resolved, id);
    assert.equal(claims.length, count);
    assert.equal(row.kind, "architecture");
    assert.equal(row.maturity, "contested");
    assert.equal(row.evidence, "contested");
    assert.equal(row.reviewed_on, "2026-09-26");
    assert.equal(
      row.evidence_scope,
      "Claim under dispute; this listing is not validation.",
    );
    assert.equal(
      findRequired(original.records, (record) => record.id === id)
        .complete_entry_review,
      false,
    );
    assert.ok(
      claims.every(
        (claim) =>
          claim.source_captured_at === null &&
          claim.source_capture_method === "retained-source-review",
      ),
    );
    for (const claim of claims.filter(
      (item) => item.topic !== "classification",
    )) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  const pd = getRequired(resolved, "palladium-deuterium-electrochemical-lenr");
  const doe = findRequired(
    pd,
    (claim) =>
      claim.source_id === "doe-cold-fusion1989" && claim.topic === "strength",
  );
  assert.deepEqual(doe.pdf_pages, [15]);
  assert.deepEqual(doe.printed_pages, ["Internet edition 4 of 5"]);
  assert.match(doe.scope, /methodological strength/);
  const gas = findRequired(
    getRequired(resolved, "gas-loaded-metal-hydrogen-lenr"),
    (claim) =>
      claim.source_id === "callisto-pressure-loading2024" &&
      claim.topic === "challenge",
  );
  assert.match(gas.scope, /belief rather than a proven fact/);
  assert.match(gas.scope, /omitted report sections/);
  const cavitation = getRequired(resolved, "cavitation-bubble-fusion");
  assert.match(
    findRequired(cavitation, (claim) => claim.topic === "strength").scope,
    /prospective success criteria/,
  );
  assert.match(
    findRequired(cavitation, (claim) => claim.topic === "challenge").scope,
    /No tritium measurement/,
  );
  const claimSource = findRequired(
    original.sources,
    (source) => source.id === "cavitation-claim2012",
  );
  assert.equal(
    claimSource.sha256,
    "2eb61f279817ba5f89c7fa574b77dedca85ebfd3a2746f5f1363af6eb84468b8",
  );
  assert.match(
    findRequired(cavitation, (claim) => claim.topic === "classification").scope,
    /not independently accepted operation/,
  );
});

test("space propulsion sources preserve ground-test, modeled-engine and ion-test boundaries", () => {
  const resolved = readCitations(root, rows);
  const ids = [
    "solid-core-nuclear-thermal-rocket",
    "fission-fragment-propulsion-reactor",
    "antiproton-catalysed-microfission-fusion",
    "direct-fusion-drive",
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
    assert.ok(
      claims.every(
        (claim) =>
          claim.source_capture_method === "publisher-tls" &&
          claim.source_captured_at !== null &&
          claim.source_captured_at.startsWith("2026-10-02T"),
      ),
    );
    for (const claim of claims.filter(
      (item) => item.topic !== "classification",
    )) {
      assert.equal(claim.statement, physicalField(row, claim.topic));
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  const rocket = getRequired(resolved, ids[0]);
  const principle = findRequired(
    rocket,
    (claim) => claim.topic === "principle",
  );
  assert.deepEqual(principle.pdf_pages, [9]);
  assert.deepEqual(principle.printed_pages, ["3"]);
  assert.match(
    findRequired(rocket, (claim) => claim.topic === "strength").scope,
    /fuel-test assembly, not a rocket engine/,
  );
  const fragments = getRequired(resolved, ids[1]);
  assert.match(
    findRequired(fragments, (claim) => claim.topic === "classification").scope,
    /modeled designs, not a built engine/,
  );
  assert.match(
    findRequired(fragments, (claim) => claim.topic === "challenge").scope,
    /Appendix A is referenced but absent/,
  );
  const antimatter = getRequired(resolved, ids[2]);
  assert.match(
    findRequired(antimatter, (claim) => claim.topic === "challenge").scope,
    /positive hydrogen ions, not stored antiprotons/,
  );
  const direct = getRequired(resolved, ids[3]);
  assert.match(
    findRequired(direct, (claim) => claim.topic === "strength").scope,
    /projected design budgets, not measured/,
  );
  assert.match(
    findRequired(direct, (claim) => claim.topic === "challenge").scope,
    /historical report/,
  );
  assert.equal(
    findRequired(rows, (row) => row.id === ids[3]).parent_id,
    "field-reversed-configuration-frc",
  );
  assert.equal(
    findRequired(rows, (row) => row.id === ids[0]).kind,
    "application architecture",
  );
});
