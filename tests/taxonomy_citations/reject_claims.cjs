// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — reject damaged claims in complete original metadata.
"use strict";

const {
  runDamageCases,
  findRequired,
} = require("../taxonomy_citation_fixture.cjs");

/** @type {import("../taxonomy_citation_fixture.cjs").DamageCase[]} */
const cases = [
  [
    "non-text citation topic",
    (d) => {
      Object.assign(d.records[0].citations[0], { topic: 12 });
    },
    /topic or identity mismatch/,
  ],
  [
    "non-text citation source",
    (d) => {
      Object.assign(d.records[0].citations[0], { source_id: 12 });
    },
    /unknown source ID/,
  ],
  [
    "numeric-string PDF page",
    (d) => {
      Object.assign(d.records[0].citations[0], { pdf_pages: ["11"] });
    },
    /outside source/,
  ],
  [
    "invented XML PDF pages",
    (d) => {
      const c = findRequired(
        d.records,
        (r) => r.id === "electrochemically-loaded-beam-target-fusion",
      ).citations[0];
      c.pdf_pages = [1];
      c.printed_pages = ["1"];
    },
    /inconsistent page locator/,
  ],
  [
    "invented XML printed label",
    (d) => {
      findRequired(
        d.records,
        (r) => r.id === "electrochemically-loaded-beam-target-fusion",
      ).citations[0].printed_pages = ["1"];
    },
    /inconsistent page locator/,
  ],
  [
    "unknown citation field",
    (d) => {
      Object.assign(d.records[0].citations[0], { approved: true });
    },
    /unexpected fields/,
  ],
  [
    "duplicate citation",
    (d) => {
      d.records[0].citations.push(d.records[0].citations[0]);
    },
    /duplicate citation ID/,
  ],
  [
    "blank citation ID",
    (d) => {
      d.records[0].citations[0].id = "";
    },
    /single-line text/,
  ],
  [
    "unknown topic",
    (d) => {
      d.records[0].citations[0].topic = "complete-physical-review";
    },
    /topic or identity mismatch/,
  ],
  [
    "wrong claim identity",
    (d) => {
      d.records[0].citations[0].id = "bwr:classification:99";
    },
    /topic or identity mismatch/,
  ],
  [
    "blank statement",
    (d) => {
      d.records[0].citations[0].statement = "";
    },
    /single-line text/,
  ],
  [
    "partial principle statement",
    (d) => {
      findRequired(
        d.records[0].citations,
        (c) => c.topic === "principle",
      ).statement = "A water-cooled reactor.";
    },
    /complete physical field/,
  ],
  [
    "changed strength statement",
    (d) => {
      findRequired(
        findRequired(d.records, (r) => r.id === "bwr").citations,
        (c) => c.topic === "strength",
      ).statement += " is cheapest";
    },
    /complete physical field/,
  ],
  [
    "incomplete challenge statement",
    (d) => {
      findRequired(
        findRequired(d.records, (r) => r.id === "lead-fast-reactor").citations,
        (c) => c.topic === "challenge",
      ).statement = "Corrosion";
    },
    /complete physical field/,
  ],
  [
    "blank section",
    (d) => {
      d.records[0].citations[0].section = "";
    },
    /single-line text/,
  ],
  [
    "blank scope",
    (d) => {
      d.records[0].citations[0].scope = "";
    },
    /single-line text/,
  ],
  [
    "false review basis",
    (d) => {
      Object.assign(d.records[0].citations[0], {
        review_basis: "independent-acceptance",
      });
    },
    /unsupported review basis/,
  ],
  [
    "non-text review date",
    (d) => {
      Object.assign(d.records[0].citations[0], { reviewed_on: 12 });
    },
    /invalid review date/,
  ],
  [
    "malformed review date",
    (d) => {
      d.records[0].citations[0].reviewed_on = "October 1";
    },
    /invalid review date/,
  ],
  [
    "impossible review month",
    (d) => {
      d.records[0].citations[0].reviewed_on = "2026-13-01";
    },
    /invalid review date/,
  ],
  [
    "normalised impossible day",
    (d) => {
      d.records[0].citations[0].reviewed_on = "2026-02-30";
    },
    /invalid review date/,
  ],
  [
    "unknown citation source",
    (d) => {
      d.records[0].citations[0].source_id = "unknown";
    },
    /unknown source ID/,
  ],
  [
    "review before capture",
    (d) => {
      d.records[0].citations[0].reviewed_on = "2026-09-30";
    },
    /predates source capture/,
  ],
  [
    "non-array PDF pages",
    (d) => {
      Object.assign(d.records[0].citations[0], { pdf_pages: 11 });
    },
    /expected an array/,
  ],
  [
    "non-array printed pages",
    (d) => {
      Object.assign(d.records[0].citations[0], { printed_pages: "4" });
    },
    /expected an array/,
  ],
  [
    "duplicate PDF pages",
    (d) => {
      d.records[0].citations[0].pdf_pages.push(11);
    },
    /duplicate PDF page/,
  ],
  [
    "missing PDF locator",
    (d) => {
      d.records[0].citations[0].pdf_pages = [];
    },
    /inconsistent page locator/,
  ],
  [
    "missing printed locator",
    (d) => {
      d.records[0].citations[0].printed_pages = [];
    },
    /inconsistent page locator/,
  ],
  [
    "HTML PDF locator",
    (d) => {
      findRequired(
        d.records.flatMap((r) => r.citations),
        (c) => c.source_id === "doe-downey",
      ).pdf_pages = [1];
    },
    /inconsistent page locator/,
  ],
  [
    "HTML printed locator",
    (d) => {
      findRequired(
        d.records.flatMap((r) => r.citations),
        (c) => c.source_id === "doe-downey",
      ).printed_pages = ["1"];
    },
    /inconsistent page locator/,
  ],
  [
    "fractional PDF page",
    (d) => {
      d.records[0].citations[0].pdf_pages = [1.5];
    },
    /outside source/,
  ],
  [
    "zero PDF page",
    (d) => {
      d.records[0].citations[0].pdf_pages = [0];
    },
    /outside source/,
  ],
  [
    "oversize PDF page",
    (d) => {
      d.records[0].citations[0].pdf_pages = [1000];
    },
    /outside source/,
  ],
  [
    "blank printed page",
    (d) => {
      d.records[0].citations[0].printed_pages = [""];
    },
    /single-line text/,
  ],
];
runDamageCases(cases);
