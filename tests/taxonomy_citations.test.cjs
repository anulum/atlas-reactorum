// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — complete taxonomy citation input conformance
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { readCitations } = require("../04_interactive_presentation/scripts/taxonomy_citations.cjs");
const root = path.resolve(__dirname, "..");
const input = "metadata/taxonomy_audit/claim_citations.json";
const taxonomy = "04_interactive_presentation/data/taxonomy-expanded.js";
global.window = {};
require(path.join(root, taxonomy));
const rows = window.REACTOR_TAXONOMY;
const original = JSON.parse(fs.readFileSync(path.join(root, input), "utf8"));

test("resolve every actual citation without approving any complete entry or mutating source data", () => {
  const before = JSON.stringify(rows);
  const result = readCitations(root, rows);
  assert.equal(result.size, 135);
  assert.deepEqual([...result.keys()], rows.map(row => row.id));
  assert.equal([...result.values()].filter(citations => citations.length).length, 135);
  assert.equal([...result.values()].flat().length, 599);
  assert.equal(JSON.stringify(rows), before);
  for (const record of original.records) {
    assert.equal(record.complete_entry_review, false);
    const citations = result.get(record.id);
    for (const [index, citation] of record.citations.entries()) {
      const source = original.sources.find(item => item.id === citation.source_id);
      assert.deepEqual(citations[index], { ...citation, source_title: source.title, source_url: source.url, source_sha256: source.sha256,
        source_capture_method: source.capture_method, source_captured_at: source.captured_at });
    }
  }
  assert.deepEqual(result.get("subcritical-assembly")[0].pdf_pages, [13]);
  assert.deepEqual(result.get("subcritical-assembly")[0].printed_pages, ["3"]);
  assert.match(result.get("subcritical-assembly")[0].scope, /not a claim that every assembly/);
});

test("chemical entries retain operating modes and resolve model, exothermic and staged-process boundaries", () => {
  const resolved = readCitations(root, rows);
  const expected = {
    "batch-reactor": ["operating mode", 4],
    "semi-batch-reactor": ["operating mode", 4],
    "continuous-stirred-tank-reactor-cstr": ["architecture", 6],
    "plug-flow-tubular-reactor": ["architecture", 5],
    "cstr-cascade": ["configuration", 6],
  };
  for (const [id, [kind, count]] of Object.entries(expected)) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id);
    assert.equal(row.kind, kind);
    assert.equal(row.maturity, "deployed");
    assert.equal(row.evidence, "established");
    assert.equal(claims.length, count);
    assert.deepEqual([...new Set(claims.map(claim => claim.topic))], ["principle", "strength", "challenge"]);
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.equal(claim.source_capture_method, "publisher-tls");
      assert.match(claim.source_captured_at, /^2026-10-01T/);
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const batch = resolved.get("batch-reactor");
  assert.deepEqual(batch[0].pdf_pages, [1, 2]);
  assert.deepEqual(batch[0].printed_pages, ["unnumbered first page", "2"]);
  assert.match(rows.find(row => row.id === "batch-reactor").challenge, /exothermic/);
  const semi = resolved.get("semi-batch-reactor").find(claim => claim.topic === "challenge");
  assert.deepEqual(semi.pdf_pages, [24, 27, 28, 35]);
  assert.match(semi.scope, /does not completely stop reaction/);
  assert.match(rows.find(row => row.id === "continuous-stirred-tank-reactor-cstr").principle, /ideal well-mixed model/);
  assert.match(rows.find(row => row.id === "plug-flow-tubular-reactor").principle, /ideal plug-flow model/);
  const cascade = resolved.get("cstr-cascade");
  assert.equal(rows.find(row => row.id === "cstr-cascade").parent_id, "continuous-stirred-tank-reactor-cstr");
  assert.match(cascade.find(claim => claim.source_id === "squ-step-feed").scope, /no advantage over a single reactor/);
  assert.match(cascade.find(claim => claim.source_id === "ima-reactive-crystallisation").scope, /burst interstage pumping/);
  assert.match(cascade.find(claim => claim.source_id === "uow-two-cstr-abstract").scope, /two physical CSTRs/);
  assert.deepEqual(cascade.find(claim => claim.source_id === "buffalo-networks").pdf_pages, [2, 3, 4]);
});

test("heavy-water and graphite claims resolve complete fields, irregular scanned pages and bounded historical evidence", () => {
  const resolved = readCitations(root, rows);
  const expected = {
    "phwr-candu": [[11, 26], [26, 31], [127, 128, 156, 157]],
    "heavy-water-pressure-vessel-reactor": [[87, 88, 90, 91], [11, 88, 102], [95, 102, 156, 157]],
    "magnox-gas-cooled-reactor": [[197], [73], [74, 75, 84, 201]],
    "advanced-gas-cooled-reactor-agr": [[], [], []],
    "rbmk-pressure-tube-reactor": [[113], [18], [13, 14, 138]],
  };
  for (const [id, pages] of Object.entries(expected)) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id).filter(claim => ["principle", "strength", "challenge"].includes(claim.topic));
    assert.deepEqual(claims.map(claim => claim.topic), ["principle", "strength", "challenge"]);
    assert.deepEqual(claims.map(claim => claim.pdf_pages), pages);
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.ok(claim.section.length && claim.scope.length);
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const magnox = resolved.get("magnox-gas-cooled-reactor").filter(claim => claim.topic !== "classification");
  assert.deepEqual(magnox.map(claim => claim.printed_pages), [["204"], ["71"], ["72", "73", "82", "208"]]);
  assert.ok(magnox.every(claim => claim.source_captured_at === null && claim.source_capture_method === "retained-source-review"));
  const agr = resolved.get("advanced-gas-cooled-reactor-agr").filter(claim => claim.topic !== "classification");
  assert.ok(agr.every(claim => claim.source_capture_method === "publisher-tls" && claim.source_captured_at !== null));
  assert.match(agr.find(claim => claim.topic === "challenge").scope, /Sizewell B/);
  assert.match(rows.find(row => row.id === "heavy-water-pressure-vessel-reactor").challenge, /fuel-channel materials degradation/);
  assert.match(resolved.get("rbmk-pressure-tube-reactor").find(claim => claim.topic === "challenge").scope, /not universal present-day/);
});

test("research configurations resolve field sources and retain geometry, criticality and named-facility boundaries", () => {
  const result = readCitations(root, rows);
  const ids = ["pool-type-research-reactor", "tank-type-research-reactor", "tank-in-pool-research-reactor",
    "aqueous-homogeneous-reactor", "critical-assembly", "subcritical-assembly", "pulsed-research-reactor"];
  for (const id of ids) {
    const row = rows.find(item => item.id === id);
    const physical = result.get(id).filter(claim => ["principle", "strength", "challenge"].includes(claim.topic));
    assert.deepEqual(physical.map(claim => claim.topic), ["principle", "strength", "challenge"]);
    for (const claim of physical) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.equal(claim.source_capture_method, "publisher-tls");
      assert.ok(claim.source_captured_at !== null);
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const tankPool = result.get("tank-in-pool-research-reactor").find(claim => claim.topic === "strength");
  assert.match(tankPool.scope, /not an attribute of every tank-in-pool/);
  assert.deepEqual(tankPool.pdf_pages, [21]);
  assert.deepEqual(tankPool.printed_pages, ["21"]);
  const aqueous = result.get("aqueous-homogeneous-reactor").find(claim => claim.topic === "challenge");
  assert.deepEqual(aqueous.pdf_pages, [12, 13, 14, 15]);
  assert.deepEqual(aqueous.printed_pages, ["5", "6", "7", "8"]);
  assert.match(result.get("aqueous-homogeneous-reactor").find(claim => claim.topic === "strength").scope, /Uniform gas, density or neutron distributions/);
  const critical = result.get("critical-assembly").find(claim => claim.topic === "challenge");
  assert.match(critical.source_url, /epfl\.ch\/labs\/lrs\/facilities\/crocus-reactor\//);
  assert.match(critical.scope, /not legal verification/);
  assert.deepEqual(critical.pdf_pages, []);
  const subcritical = result.get("subcritical-assembly").find(claim => claim.topic === "challenge");
  assert.match(subcritical.scope, /independently of source characteristics/);
  const pulse = result.get("pulsed-research-reactor").find(claim => claim.topic === "principle");
  assert.match(pulse.source_url, /triga\.uni-mainz\.de\/betriebsmodus\//);
  assert.match(pulse.scope, /not universal pulse capability/);
});

test("electrochemical field sources retain reaction, page and energy-accounting boundaries", () => {
  const result = readCitations(root, rows);
  const ids = ["alkaline-water-electrolyser", "pem-water-electrolyser", "solid-oxide-electrolyser", "anion-exchange-membrane-electrolyser",
    "pem-fuel-cell", "alkaline-fuel-cell", "phosphoric-acid-fuel-cell", "molten-carbonate-fuel-cell", "solid-oxide-fuel-cell"];
  for (const id of ids) {
    const row = rows.find(item => item.id === id);
    const claims = result.get(id).filter(claim => ["principle", "strength", "challenge"].includes(claim.topic));
    assert.deepEqual(claims.map(claim => claim.topic), ["principle", "strength", "challenge"]);
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
      assert.equal(claim.source_capture_method, "publisher-tls");
      assert.ok(claim.source_captured_at !== null);
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const oxide = result.get("solid-oxide-electrolyser");
  const reaction = oxide.find(claim => claim.topic === "principle");
  assert.deepEqual(reaction.pdf_pages, [6, 8]);
  assert.deepEqual(reaction.printed_pages, ["1", "3"]);
  assert.match(reaction.source_title, /H2O-CO2 Co-Electrolysis/);
  assert.match(oxide.find(claim => claim.topic === "strength").scope, /does not remove the heat input/);
  const pem = result.get("pem-water-electrolyser").find(claim => claim.topic === "principle");
  assert.deepEqual(pem.pdf_pages, []);
  assert.match(pem.source_url, /hydrogen-production-electrolysis/);
  const alkaline = result.get("alkaline-fuel-cell").find(claim => claim.topic === "principle");
  assert.deepEqual(alkaline.pdf_pages, [115]);
  assert.deepEqual(alkaline.printed_pages, ["4-3"]);
  const acid = result.get("phosphoric-acid-fuel-cell").find(claim => claim.topic === "challenge");
  assert.deepEqual(acid.pdf_pages, [30, 134]);
  assert.deepEqual(acid.printed_pages, ["1-11", "5-5"]);
  assert.match(acid.scope, /not a demonstrated universal current stack lifetime/);
  assert.match(result.get("anion-exchange-membrane-electrolyser").find(claim => claim.topic === "strength").scope, /not universal PGM-free commercial operation/);
});

test("physical claims bind the complete actual field and distinguish retained NRC originals from publisher captures", () => {
  const result = readCitations(root, rows);
  const physical = [...result.values()].flat().filter(citation => ["principle", "strength", "challenge"].includes(citation.topic));
  assert.equal(physical.length, 480);
  for (const row of rows) {
    for (const citation of result.get(row.id).filter(item => ["principle", "strength", "challenge"].includes(item.topic))) {
      assert.equal(citation.statement, row[citation.topic]);
      assert.ok(row.source_urls.includes(citation.source_url));
    }
  }
  const retained = physical.filter(citation => citation.source_capture_method === "retained-source-review");
  assert.equal(retained.length, 146);
  assert.ok(retained.every(citation => citation.source_captured_at === null));
  const nrc = retained.filter(citation => citation.source_title.startsWith("NRC") || citation.source_title.startsWith("Reactor Concepts Manual"));
  assert.equal(nrc.length, 7);
  assert.ok(nrc.every(citation => citation.source_captured_at === null));
  const pwr = result.get("pwr").find(citation => citation.topic === "principle");
  assert.deepEqual(pwr.pdf_pages, [75, 76]);
  assert.deepEqual(pwr.printed_pages, ["75", "76"]);
  const bwr = result.get("bwr").filter(citation => citation.topic === "principle");
  assert.deepEqual(bwr.map(citation => citation.pdf_pages), [[21], [2]]);
  assert.deepEqual(bwr.map(citation => citation.printed_pages), [["21"], ["3-2"]]);
  const integral = result.get("integral-pwr").find(citation => citation.topic === "principle");
  assert.match(integral.statement, /^Most or all primary system components/);
  assert.equal(integral.source_capture_method, "publisher-tls");
  assert.deepEqual(integral.pdf_pages, [20, 146]);
  assert.match(integral.scope, /educational evidence/);
});

test("all six HTGR and fast-reactor entries expose full-field locators without changing their maturity or approving deployment", () => {
  const result = readCitations(root, rows);
  const expected = {
    "prismatic-htgr": [[13], [13, 19, 25], [19, 135]],
    "pebble-bed-htgr": [[13, 140], [13, 140], [60, 64, 66]],
    "sodium-fast-reactor": [[212, 219, 550], [15, 212, 221], [559, 757]],
    "lead-fast-reactor": [[285], [285], [285, 286, 287]],
    "lead-bismuth-fast-reactor": [[285], [285, 286], [286, 287]],
    "gas-cooled-fast-reactor": [[342, 344, 363], [343], [342, 360]],
  };
  for (const [id, locators] of Object.entries(expected)) {
    const row = rows.find(item => item.id === id);
    const claims = result.get(id);
    assert.deepEqual(claims.map(citation => citation.topic), ["principle", "strength", "challenge"]);
    assert.deepEqual(claims.map(citation => citation.pdf_pages), locators);
    assert.ok(claims.every(citation => citation.source_captured_at === null && citation.source_capture_method === "retained-source-review"));
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.deepEqual(claim.printed_pages, claim.pdf_pages.map(page => String(page - (id.includes("htgr") ? 8 : 13))));
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  assert.equal(rows.find(row => row.id === "sodium-fast-reactor").principle, "Liquid sodium cools a fast-neutron core.");
  assert.match(result.get("sodium-fast-reactor")[0].scope, /hydride shielding/);
  assert.match(rows.find(row => row.id === "gas-cooled-fast-reactor").principle, /designs target refractory fuel/);
  assert.match(result.get("gas-cooled-fast-reactor")[0].scope, /conventional MOX and steel cladding/);
  assert.match(rows.find(row => row.id === "gas-cooled-fast-reactor").strength, /^Targeted /);
});

test("GIF SCWR and VHTR resolve actual full fields with HTML headings and known retrieval dates while keeping design potential explicit", () => {
  const resolved = readCitations(root, rows);
  const expected = [
    ["supercritical-water-reactor", "gif-scwr"],
    ["very-high-temperature-reactor-vhtr", "gif-vhtr"],
  ];
  for (const [id, sourceId] of expected) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id);
    assert.deepEqual(claims.map(claim => claim.topic), ["principle", "strength", "challenge"]);
    const source = original.sources.find(item => item.id === sourceId);
    assert.equal(source.format, "html");
    assert.equal(source.page_count, 0);
    assert.equal(source.capture_method, "publisher-tls");
    assert.match(source.captured_at, /^2026-10-01T/);
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.equal(claim.source_url, source.url);
      assert.ok(row.source_urls.includes(source.url));
      assert.equal(claim.source_sha256, source.sha256);
      assert.equal(claim.source_captured_at, source.captured_at);
      assert.deepEqual(claim.pdf_pages, []);
      assert.deepEqual(claim.printed_pages, []);
      assert.ok(claim.section.length > 0);
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
    assert.equal(row.maturity, "concept");
    assert.equal(row.evidence, "research");
  }
  assert.match(resolved.get("supercritical-water-reactor")[1].scope, /not measured SCWR plant output/);
  assert.match(resolved.get("very-high-temperature-reactor-vhtr")[0].scope, /lower-temperature HTGR examples/);
  assert.match(rows.find(row => row.id === "very-high-temperature-reactor-vhtr").strength, /^Potential /);
  assert.match(resolved.get("very-high-temperature-reactor-vhtr")[2].scope, /does not establish lifetime/);
});

test("salt entries distinguish liquid fuel from fluoride coolant with retained IAEA locators and pending complete review", () => {
  const resolved = readCitations(root, rows);
  const expected = {
    "thermal-liquid-fuel-molten-salt-reactor": [[54, 68], [23, 24], [29, 30, 31, 33, 34]],
    "fast-liquid-fuel-molten-salt-reactor": [[60, 64, 75], [61, 65, 75, 76], [29, 32, 34, 60, 65, 76]],
    "fluoride-salt-cooled-high-temperature-reactor": [[51, 52], [51, 52], [29, 34, 52]],
  };
  for (const [id, pages] of Object.entries(expected)) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id).filter(claim => ["principle", "strength", "challenge"].includes(claim.topic));
    assert.deepEqual(claims.map(claim => claim.topic), ["principle", "strength", "challenge"]);
    assert.deepEqual(claims.map(claim => claim.pdf_pages), pages);
    for (const claim of claims) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.equal(claim.source_capture_method, "retained-source-review");
      assert.equal(claim.source_captured_at, null);
      assert.deepEqual(claim.printed_pages, claim.pdf_pages.map(page => String(page - 10)));
      assert.ok(row.source_urls.includes(claim.source_url));
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const coolant = resolved.get("fluoride-salt-cooled-high-temperature-reactor").find(claim => claim.topic === "fuel-state-classification");
  assert.equal(coolant.source_url, "https://www-pub.iaea.org/MTCD/Publications/PDF/TE_1696_web.pdf");
  assert.deepEqual(coolant.pdf_pages, [28]);
  assert.deepEqual(coolant.printed_pages, ["16"]);
  assert.equal(coolant.source_captured_at, null);
  assert.match(rows.find(row => row.id === "thermal-liquid-fuel-molten-salt-reactor").principle, /moderated thermal-neutron core/);
  assert.match(resolved.get("thermal-liquid-fuel-molten-salt-reactor")[0].scope, /circulation is not universal/);
  assert.match(rows.find(row => row.id === "fast-liquid-fuel-molten-salt-reactor").strength, /^Potential /);
  assert.match(resolved.get("fast-liquid-fuel-molten-salt-reactor")[2].scope, /not an attribute of every fast MSR/);
  assert.match(rows.find(row => row.id === "fluoride-salt-cooled-high-temperature-reactor").challenge, /decay-heat removal/);
});

test("externally driven fusion fields retain observed-mechanism, loading and neutron-spectrum boundaries", () => {
  const result = readCitations(root, rows);
  for (const id of ["muon-catalysed-fusion", "lattice-confinement-fusion", "electrochemically-loaded-beam-target-fusion", "pyroelectric-fusion-source"]) {
    const row = rows.find(item => item.id === id);
    const claims = result.get(id);
    assert.deepEqual([...new Set(claims.map(claim => claim.topic))], ["classification", "principle", "strength", "challenge"]);
    for (const claim of claims.filter(claim => claim.topic !== "classification")) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
    }
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
  }
  const muon = result.get("muon-catalysed-fusion");
  assert.equal(muon[0].source_title, "Muon Catalyzed Fusion");
  assert.deepEqual(muon.find(claim => claim.topic === "challenge").printed_pages, ["218", "219"]);
  assert.match(muon.find(claim => claim.topic === "challenge").scope, /historical/);
  assert.match(rows.find(row => row.id === "lattice-confinement-fusion").challenge, /resolving higher-energy neutron sources/);
  const xml = original.sources.find(source => source.id === "beam-chen2025");
  assert.equal(xml.format, "xml");
  assert.equal(xml.page_count, 0);
  assert.equal(xml.sha256, "418993afce3145dc14c2865da34c1f9abb91d660cd1eb29d0237fbdf10896352");
  for (const claim of result.get("electrochemically-loaded-beam-target-fusion")) {
    assert.deepEqual(claim.pdf_pages, []);
    assert.deepEqual(claim.printed_pages, []);
    assert.equal(claim.source_url, xml.url);
    assert.match(claim.section, /Sec[1-5]/);
  }
  assert.match(result.get("electrochemically-loaded-beam-target-fusion").find(claim => claim.topic === "strength").scope, /could not measure the D\/Pd ratio directly/);
  assert.match(result.get("pyroelectric-fusion-source").find(claim => claim.topic === "challenge").scope, /externally supplied heating\/cooling/);
});

test("contested nuclear fields expose named null tests and prospective criteria without accepting nuclear output", () => {
  const resolved = readCitations(root, rows);
  const counts = { "palladium-deuterium-electrochemical-lenr": 8, "gas-loaded-metal-hydrogen-lenr": 5, "cavitation-bubble-fusion": 5 };
  for (const [id, count] of Object.entries(counts)) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id);
    assert.equal(claims.length, count);
    assert.equal(row.kind, "architecture");
    assert.equal(row.maturity, "contested");
    assert.equal(row.evidence, "contested");
    assert.equal(row.reviewed_on, "2026-09-26");
    assert.equal(row.evidence_scope, "Claim under dispute; this listing is not validation.");
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
    assert.ok(claims.every(claim => claim.source_captured_at === null && claim.source_capture_method === "retained-source-review"));
    for (const claim of claims.filter(item => item.topic !== "classification")) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  const pd = resolved.get("palladium-deuterium-electrochemical-lenr");
  const doe = pd.find(claim => claim.source_id === "doe-cold-fusion1989" && claim.topic === "strength");
  assert.deepEqual(doe.pdf_pages, [15]);
  assert.deepEqual(doe.printed_pages, ["Internet edition 4 of 5"]);
  assert.match(doe.scope, /methodological strength/);
  const gas = resolved.get("gas-loaded-metal-hydrogen-lenr").find(claim => claim.source_id === "callisto-pressure-loading2024" && claim.topic === "challenge");
  assert.match(gas.scope, /belief rather than a proven fact/);
  assert.match(gas.scope, /omitted report sections/);
  const cavitation = resolved.get("cavitation-bubble-fusion");
  assert.match(cavitation.find(claim => claim.topic === "strength").scope, /prospective success criteria/);
  assert.match(cavitation.find(claim => claim.topic === "challenge").scope, /No tritium measurement/);
  const claimSource = original.sources.find(source => source.id === "cavitation-claim2012");
  assert.equal(claimSource.sha256, "2eb61f279817ba5f89c7fa574b77dedca85ebfd3a2746f5f1363af6eb84468b8");
  assert.match(cavitation.find(claim => claim.topic === "classification").scope, /not independently accepted operation/);
});

test("space propulsion sources preserve ground-test, modeled-engine and ion-test boundaries", () => {
  const resolved = readCitations(root, rows);
  const ids = ["solid-core-nuclear-thermal-rocket", "fission-fragment-propulsion-reactor", "antiproton-catalysed-microfission-fusion", "direct-fusion-drive"];
  for (const id of ids) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id);
    assert.equal(claims.length, 4);
    assert.equal(row.reviewed_on, "2026-09-26");
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
    assert.ok(claims.every(claim => claim.source_capture_method === "publisher-tls" && claim.source_captured_at.startsWith("2026-10-02T")));
    for (const claim of claims.filter(item => item.topic !== "classification")) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  const rocket = resolved.get(ids[0]);
  const principle = rocket.find(claim => claim.topic === "principle");
  assert.deepEqual(principle.pdf_pages, [9]);
  assert.deepEqual(principle.printed_pages, ["3"]);
  assert.match(rocket.find(claim => claim.topic === "strength").scope, /fuel-test assembly, not a rocket engine/);
  const fragments = resolved.get(ids[1]);
  assert.match(fragments.find(claim => claim.topic === "classification").scope, /modeled designs, not a built engine/);
  assert.match(fragments.find(claim => claim.topic === "challenge").scope, /Appendix A is referenced but absent/);
  const antimatter = resolved.get(ids[2]);
  assert.match(antimatter.find(claim => claim.topic === "challenge").scope, /positive hydrogen ions, not stored antiprotons/);
  const direct = resolved.get(ids[3]);
  assert.match(direct.find(claim => claim.topic === "strength").scope, /projected design budgets, not measured/);
  assert.match(direct.find(claim => claim.topic === "challenge").scope, /historical report/);
  assert.equal(rows.find(row => row.id === ids[3]).parent_id, "field-reversed-configuration-frc");
  assert.equal(rows.find(row => row.id === ids[0]).kind, "application architecture");
});

test("solar, plasma and bioelectrochemical citations retain their actual energy and source boundaries", () => {
  const resolved = readCitations(root, rows);
  const ids = ["solar-thermochemical-redox-reactor", "plasma-catalytic-reactor", "photovoltaic-photothermal-artificial-photosynthesis", "microbial-fuel-cell", "microbial-electrolysis-cell"];
  for (const id of ids) {
    const row = rows.find(item => item.id === id);
    const claims = resolved.get(id);
    assert.equal(claims.length, 4);
    assert.equal(row.reviewed_on, "2026-09-26");
    assert.equal(original.records.find(record => record.id === id).complete_entry_review, false);
    for (const claim of claims.filter(item => item.topic !== "classification")) {
      assert.equal(claim.statement, row[claim.topic]);
      assert.ok(row.source_urls.includes(claim.source_url));
    }
  }
  assert.match(resolved.get(ids[0]).find(c => c.topic === "challenge").scope, /local ceria cracking/);
  assert.match(resolved.get(ids[1]).find(c => c.topic === "challenge").scope, /Three GC injections/);
  assert.equal(rows.find(r => r.id === ids[2]).kind, "system integration");
  assert.match(resolved.get(ids[2]).find(c => c.topic === "challenge").scope, /allocated PV area/);
  for (const id of ids.slice(3)) {
    for (const claim of resolved.get(id)) {
      assert.deepEqual(claim.pdf_pages, []);
      assert.deepEqual(claim.printed_pages, []);
      assert.match(claim.source_url, /europepmc\/webservices\/rest\/PMC[0-9]+\/fullTextXML$/);
      const source = original.sources.find(s => s.id === claim.source_id);
      assert.equal(source.format, "xml");
      assert.equal(source.page_count, 0);
    }
  }
  assert.equal(rows.find(r => r.id === ids[4]).challenge, "Catalyst poisoning and full-system energy accounting");
  assert.match(resolved.get(ids[4]).find(c => c.topic === "challenge").scope, /substrate chemical energy/);
});

const damageCases = [
  ["XML page count", d => { d.sources.find(s => s.id === "beam-chen2025").page_count = 1; }, /invalid page count/],
  ["invented XML PDF pages", d => { const c = d.records.find(r => r.id === "electrochemically-loaded-beam-target-fusion").citations[0]; c.pdf_pages = [1]; c.printed_pages = ["1"]; }, /inconsistent page locator/],
  ["invented XML printed label", d => { d.records.find(r => r.id === "electrochemically-loaded-beam-target-fusion").citations[0].printed_pages = ["1"]; }, /inconsistent page locator/],
  ["null document", d => null, /expected an object/],
  ["array document", d => [], /expected an object/],
  ["scalar document", d => 1, /expected an object/],
  ["extra document field", d => { d.approved = true; }, /unexpected fields/],
  ["schema", d => { d.schema_version = "0.0.0"; }, /unsupported schema/],
  ["stale hash", d => { d.taxonomy_sha256 = "0".repeat(64); }, /stale taxonomy hash/],
  ["non-array sources", d => { d.sources = {}; }, /expected an array/],
  ["non-array records", d => { d.records = {}; }, /expected an array/],
  ["partial catalogue", d => { d.records.pop(); }, /incomplete entry set/],
  ["null source", d => { d.sources[0] = null; }, /expected an object/],
  ["extra source field", d => { d.sources[0].permission = true; }, /unexpected fields/],
  ["non-text source ID", d => { d.sources[0].id = 12; }, /single-line text/],
  ["empty source ID", d => { d.sources[0].id = ""; }, /single-line text/],
  ["padded title", d => { d.sources[0].title += " "; }, /single-line text/],
  ["multiline title", d => { d.sources[0].title += "\nnext"; }, /single-line text/],
  ["duplicate source", d => { d.sources.push(d.sources[0]); }, /duplicate source ID/],
  ["non-text URL", d => { d.sources[0].url = null; }, /single-line text/],
  ["non-HTTPS URL", d => { d.sources[0].url = d.sources[0].url.replace("https:", "http:"); }, /anonymous HTTPS/],
  ["credentialed URL", d => { d.sources[0].url = "https://user@example.org/document"; }, /anonymous HTTPS/],
  ["non-text SHA", d => { d.sources[0].sha256 = 12; }, /invalid SHA-256/],
  ["bad SHA", d => { d.sources[0].sha256 = "z".repeat(64); }, /invalid SHA-256/],
  ["non-text capture", d => { d.sources[0].captured_at = 12; }, /invalid UTC/],
  ["naive capture", d => { d.sources[0].captured_at = "2026-10-01T03:00:00"; }, /invalid UTC/],
  ["impossible capture", d => { d.sources[0].captured_at = "2026-13-01T03:00:00Z"; }, /invalid UTC/],
  ["normalised impossible capture day", d => { d.sources[0].captured_at = "2026-02-30T03:00:00Z"; }, /invalid UTC/],
  ["missing publisher capture", d => { d.sources[0].captured_at = null; }, /invalid UTC/],
  ["unknown capture method", d => { d.sources[0].capture_method = "live-verified"; }, /unsupported capture method/],
  ["non-text capture method", d => { d.sources[0].capture_method = null; }, /unsupported capture method/],
  ["invented retained capture time", d => { d.sources.find(s => s.id === "nrc-r100").captured_at = "2026-10-01T05:00:00Z"; }, /original capture time is unknown/],
  ["retained source promoted to publisher capture", d => { d.sources.find(s => s.id === "nrc-r100").capture_method = "publisher-tls"; }, /invalid UTC/],
  ["unsupported custody", d => { d.sources[0].access = "redistribution approved"; }, /unsupported custody claim/],
  ["unsupported format", d => { d.sources[0].format = "zip"; }, /unsupported format/],
  ["fractional page count", d => { d.sources[0].page_count = 0.5; }, /invalid page count/],
  ["HTML page count", d => { d.sources.find(s => s.format === "html").page_count = 1; }, /invalid page count/],
  ["PDF page count", d => { d.sources.find(s => s.format === "pdf").page_count = 0; }, /invalid page count/],
  ["unknown entry field", d => { d.records[0].accepted = true; }, /unexpected fields/],
  ["blank entry ID", d => { d.records[0].id = ""; }, /single-line text/],
  ["unknown entry ID", d => { d.records[0].id += "-unknown"; }, /identity or order mismatch/],
  ["swapped entries", d => { [d.records[0], d.records[1]] = [d.records[1], d.records[0]]; }, /identity or order mismatch/],
  ["unknown bound field", d => { d.records[0].values.capacity = 1; }, /unexpected fields/],
  ["object-valued kind", d => { d.records[0].values.kind = {}; }, /Bound taxonomy kind: expected nonempty single-line text/],
  ["empty bound name", d => { d.records[0].values.name = ""; }, /Bound taxonomy name: expected nonempty single-line text/],
  ["multiline bound principle", d => { d.records[0].values.principle += "\nnext"; }, /Bound taxonomy principle: expected nonempty single-line text/],
  ["non-array bound references", d => { d.records[0].values.source_urls = {}; }, /Bound taxonomy source URLs: expected an array/],
  ["empty bound references", d => { d.records[0].values.source_urls = []; }, /Bound taxonomy: missing source URLs/],
  ["non-text bound reference", d => { d.records[0].values.source_urls[0] = null; }, /Source URL: expected nonempty single-line text/],
  ["non-HTTPS bound reference", d => { d.records[0].values.source_urls[0] = d.records[0].values.source_urls[0].replace("https:", "http:"); }, /Source URL: expected anonymous HTTPS/],
  ["changed physical wording", d => { d.records[0].values.principle += " changed"; }, /changed taxonomy values/],
  ["changed reference", d => { d.records[0].values.source_urls.pop(); }, /changed taxonomy values/],
  ["invented complete review", d => { d.records[0].complete_entry_review = true; }, /not established/],
  ["non-array citations", d => { d.records[0].citations = {}; }, /expected an array/],
  ["unknown citation field", d => { d.records[0].citations[0].approved = true; }, /unexpected fields/],
  ["duplicate citation", d => { d.records[0].citations.push(d.records[0].citations[0]); }, /duplicate citation ID/],
  ["blank citation ID", d => { d.records[0].citations[0].id = ""; }, /single-line text/],
  ["unknown topic", d => { d.records[0].citations[0].topic = "complete-physical-review"; }, /topic or identity mismatch/],
  ["wrong claim identity", d => { d.records[0].citations[0].id = "bwr:classification:99"; }, /topic or identity mismatch/],
  ["blank statement", d => { d.records[0].citations[0].statement = ""; }, /single-line text/],
  ["partial principle statement", d => { d.records[0].citations.find(c => c.topic === "principle").statement = "A water-cooled reactor."; }, /complete physical field/],
  ["changed strength statement", d => { d.records.find(r => r.id === "bwr").citations.find(c => c.topic === "strength").statement += " is cheapest"; }, /complete physical field/],
  ["incomplete challenge statement", d => { d.records.find(r => r.id === "lead-fast-reactor").citations.find(c => c.topic === "challenge").statement = "Corrosion"; }, /complete physical field/],
  ["blank section", d => { d.records[0].citations[0].section = ""; }, /single-line text/],
  ["blank scope", d => { d.records[0].citations[0].scope = ""; }, /single-line text/],
  ["false review basis", d => { d.records[0].citations[0].review_basis = "independent-acceptance"; }, /unsupported review basis/],
  ["non-text review date", d => { d.records[0].citations[0].reviewed_on = 12; }, /invalid review date/],
  ["malformed review date", d => { d.records[0].citations[0].reviewed_on = "October 1"; }, /invalid review date/],
  ["impossible review month", d => { d.records[0].citations[0].reviewed_on = "2026-13-01"; }, /invalid review date/],
  ["normalised impossible day", d => { d.records[0].citations[0].reviewed_on = "2026-02-30"; }, /invalid review date/],
  ["unknown citation source", d => { d.records[0].citations[0].source_id = "unknown"; }, /unknown source ID/],
  ["review before capture", d => { d.records[0].citations[0].reviewed_on = "2026-09-30"; }, /predates source capture/],
  ["non-array PDF pages", d => { d.records[0].citations[0].pdf_pages = 11; }, /expected an array/],
  ["non-array printed pages", d => { d.records[0].citations[0].printed_pages = "4"; }, /expected an array/],
  ["duplicate PDF pages", d => { d.records[0].citations[0].pdf_pages.push(11); }, /duplicate PDF page/],
  ["missing PDF locator", d => { d.records[0].citations[0].pdf_pages = []; }, /inconsistent page locator/],
  ["missing printed locator", d => { d.records[0].citations[0].printed_pages = []; }, /inconsistent page locator/],
  ["HTML PDF locator", d => { d.records.flatMap(r => r.citations).find(c => c.source_id === "doe-downey").pdf_pages = [1]; }, /inconsistent page locator/],
  ["HTML printed locator", d => { d.records.flatMap(r => r.citations).find(c => c.source_id === "doe-downey").printed_pages = ["1"]; }, /inconsistent page locator/],
  ["fractional PDF page", d => { d.records[0].citations[0].pdf_pages = [1.5]; }, /outside source/],
  ["zero PDF page", d => { d.records[0].citations[0].pdf_pages = [0]; }, /outside source/],
  ["oversize PDF page", d => { d.records[0].citations[0].pdf_pages = [1000]; }, /outside source/],
  ["blank printed page", d => { d.records[0].citations[0].printed_pages = [""]; }, /single-line text/],
  ["unused source", d => { d.sources.push({ ...d.sources[0], id: "unused" }); }, /unused source metadata/],
];

for (const [label, change, expected] of damageCases) {
  test(`refuse ${label} in the complete actual metadata`, context => {
    const dir = fs.mkdtempSync(path.join(process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(), "atlas-citations-"));
    context.after(() => fs.rmSync(dir, { recursive: true }));
    for (const relative of [input, taxonomy]) {
      const target = path.join(dir, relative);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(path.join(root, relative), target);
    }
    let document = structuredClone(original);
    const replacement = change(document);
    if (replacement !== undefined) document = replacement;
    fs.writeFileSync(path.join(dir, input), JSON.stringify(document));
    const before = fs.readFileSync(path.join(dir, input));
    assert.throws(() => readCitations(dir, rows), expected);
    assert.deepEqual(fs.readFileSync(path.join(dir, input)), before);
  });
}

test("reject missing metadata, malformed JSON, missing taxonomy and invalid runtime catalogue", context => {
  const dir = fs.mkdtempSync(path.join(process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(), "atlas-citations-"));
  context.after(() => fs.rmSync(dir, { recursive: true }));
  fs.mkdirSync(path.join(dir, path.dirname(input)), { recursive: true });
  assert.throws(() => readCitations(dir, rows), { code: "ENOENT" });
  fs.writeFileSync(path.join(dir, input), "{");
  assert.throws(() => readCitations(dir, rows), SyntaxError);
  fs.copyFileSync(path.join(root, input), path.join(dir, input));
  assert.throws(() => readCitations(dir, rows), { code: "ENOENT" });
  assert.throws(() => readCitations(root, null), /expected an array/);
  assert.throws(() => readCitations(root, []), /incomplete entry set/);
  const duplicates = structuredClone(rows);
  duplicates[1] = duplicates[0];
  assert.throws(() => readCitations(root, duplicates), /identity or order mismatch/);
});
