// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — reject damaged entries in complete original metadata.
"use strict";

const { runDamageCases } = require("../taxonomy_citation_fixture.cjs");
const assert = require("node:assert/strict");

/** @type {import("../taxonomy_citation_fixture.cjs").DamageCase[]} */
const cases = [
  [
    "partial catalogue",
    (d) => {
      d.records.pop();
    },
    /incomplete entry set/,
  ],
  [
    "unknown entry field",
    (d) => {
      Object.assign(d.records[0], { accepted: true });
    },
    /unexpected fields/,
  ],
  [
    "blank entry ID",
    (d) => {
      d.records[0].id = "";
    },
    /single-line text/,
  ],
  [
    "unknown entry ID",
    (d) => {
      d.records[0].id += "-unknown";
    },
    /identity or order mismatch/,
  ],
  [
    "swapped entries",
    (d) => {
      [d.records[0], d.records[1]] = [d.records[1], d.records[0]];
    },
    /identity or order mismatch/,
  ],
  [
    "unknown bound field",
    (d) => {
      Object.assign(d.records[0].values, { capacity: 1 });
    },
    /unexpected fields/,
  ],
  [
    "object-valued kind",
    (d) => {
      Object.assign(d.records[0].values, { kind: {} });
    },
    /Bound taxonomy kind: expected nonempty single-line text/,
  ],
  [
    "empty bound name",
    (d) => {
      d.records[0].values.name = "";
    },
    /Bound taxonomy name: expected nonempty single-line text/,
  ],
  [
    "multiline bound principle",
    (d) => {
      d.records[0].values.principle += "\nnext";
    },
    /Bound taxonomy principle: expected nonempty single-line text/,
  ],
  [
    "non-array bound references",
    (d) => {
      Object.assign(d.records[0].values, { source_urls: {} });
    },
    /Bound taxonomy source URLs: expected an array/,
  ],
  [
    "empty bound references",
    (d) => {
      d.records[0].values.source_urls = [];
    },
    /Bound taxonomy: missing source URLs/,
  ],
  [
    "non-text bound reference",
    (d) => {
      assert.ok(Reflect.set(d.records[0].values.source_urls, 0, null));
    },
    /Source URL: expected nonempty single-line text/,
  ],
  [
    "non-HTTPS bound reference",
    (d) => {
      d.records[0].values.source_urls[0] =
        d.records[0].values.source_urls[0].replace("https:", "http:");
    },
    /Source URL: expected anonymous HTTPS/,
  ],
  [
    "changed physical wording",
    (d) => {
      d.records[0].values.principle += " changed";
    },
    /changed taxonomy values/,
  ],
  [
    "changed reference",
    (d) => {
      d.records[0].values.source_urls.pop();
    },
    /changed taxonomy values/,
  ],
  [
    "invented complete review",
    (d) => {
      Object.assign(d.records[0], { complete_entry_review: true });
    },
    /not established/,
  ],
  [
    "non-array citations",
    (d) => {
      Object.assign(d.records[0], { citations: {} });
    },
    /expected an array/,
  ],
];
runDamageCases(cases);
