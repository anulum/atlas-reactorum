// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — reject damaged sources in complete original metadata.
"use strict";

const {
  runDamageCases,
  findRequired,
} = require("../taxonomy_citation_fixture.cjs");
const assert = require("node:assert/strict");

/** @type {import("../taxonomy_citation_fixture.cjs").DamageCase[]} */
const cases = [
  [
    "numeric-string page count",
    (d) => {
      Object.assign(d.sources[0], { page_count: "11" });
    },
    /invalid page count/,
  ],
  [
    "XML page count",
    (d) => {
      findRequired(d.sources, (s) => s.id === "beam-chen2025").page_count = 1;
    },
    /invalid page count/,
  ],
  ["null document", () => null, /expected an object/],
  ["array document", () => [], /expected an object/],
  ["scalar document", () => 1, /expected an object/],
  [
    "extra document field",
    (d) => {
      Object.assign(d, { approved: true });
    },
    /unexpected fields/,
  ],
  [
    "schema",
    (d) => {
      Object.assign(d, { schema_version: "0.0.0" });
    },
    /unsupported schema/,
  ],
  [
    "stale hash",
    (d) => {
      d.taxonomy_sha256 = "0".repeat(64);
    },
    /stale taxonomy hash/,
  ],
  [
    "non-array sources",
    (d) => {
      Object.assign(d, { sources: {} });
    },
    /expected an array/,
  ],
  [
    "non-array records",
    (d) => {
      Object.assign(d, { records: {} });
    },
    /expected an array/,
  ],
  [
    "null source",
    (d) => {
      assert.ok(Reflect.set(d.sources, 0, null));
    },
    /expected an object/,
  ],
  [
    "extra source field",
    (d) => {
      Object.assign(d.sources[0], { permission: true });
    },
    /unexpected fields/,
  ],
  [
    "non-text source ID",
    (d) => {
      Object.assign(d.sources[0], { id: 12 });
    },
    /single-line text/,
  ],
  [
    "empty source ID",
    (d) => {
      d.sources[0].id = "";
    },
    /single-line text/,
  ],
  [
    "padded title",
    (d) => {
      d.sources[0].title += " ";
    },
    /single-line text/,
  ],
  [
    "multiline title",
    (d) => {
      d.sources[0].title += "\nnext";
    },
    /single-line text/,
  ],
  [
    "duplicate source",
    (d) => {
      d.sources.push(d.sources[0]);
    },
    /duplicate source ID/,
  ],
  [
    "non-text URL",
    (d) => {
      Object.assign(d.sources[0], { url: null });
    },
    /single-line text/,
  ],
  [
    "non-HTTPS URL",
    (d) => {
      d.sources[0].url = d.sources[0].url.replace("https:", "http:");
    },
    /anonymous HTTPS/,
  ],
  [
    "credentialed URL",
    (d) => {
      d.sources[0].url = "https://user@example.org/document";
    },
    /anonymous HTTPS/,
  ],
  [
    "non-text SHA",
    (d) => {
      Object.assign(d.sources[0], { sha256: 12 });
    },
    /invalid SHA-256/,
  ],
  [
    "bad SHA",
    (d) => {
      d.sources[0].sha256 = "z".repeat(64);
    },
    /invalid SHA-256/,
  ],
  [
    "non-text capture",
    (d) => {
      Object.assign(d.sources[0], { captured_at: 12 });
    },
    /invalid UTC/,
  ],
  [
    "naive capture",
    (d) => {
      d.sources[0].captured_at = "2026-10-01T03:00:00";
    },
    /invalid UTC/,
  ],
  [
    "impossible capture",
    (d) => {
      d.sources[0].captured_at = "2026-13-01T03:00:00Z";
    },
    /invalid UTC/,
  ],
  [
    "normalised impossible capture day",
    (d) => {
      d.sources[0].captured_at = "2026-02-30T03:00:00Z";
    },
    /invalid UTC/,
  ],
  [
    "missing publisher capture",
    (d) => {
      d.sources[0].captured_at = null;
    },
    /invalid UTC/,
  ],
  [
    "unknown capture method",
    (d) => {
      Object.assign(d.sources[0], { capture_method: "live-verified" });
    },
    /unsupported capture method/,
  ],
  [
    "non-text capture method",
    (d) => {
      Object.assign(d.sources[0], { capture_method: null });
    },
    /unsupported capture method/,
  ],
  [
    "invented retained capture time",
    (d) => {
      findRequired(d.sources, (s) => s.id === "nrc-r100").captured_at =
        "2026-10-01T05:00:00Z";
    },
    /original capture time is unknown/,
  ],
  [
    "retained source promoted to publisher capture",
    (d) => {
      findRequired(d.sources, (s) => s.id === "nrc-r100").capture_method =
        "publisher-tls";
    },
    /invalid UTC/,
  ],
  [
    "unsupported custody",
    (d) => {
      Object.assign(d.sources[0], { access: "redistribution approved" });
    },
    /unsupported custody claim/,
  ],
  [
    "unsupported format",
    (d) => {
      Object.assign(d.sources[0], { format: "zip" });
    },
    /unsupported format/,
  ],
  [
    "fractional page count",
    (d) => {
      d.sources[0].page_count = 0.5;
    },
    /invalid page count/,
  ],
  [
    "HTML page count",
    (d) => {
      findRequired(d.sources, (s) => s.format === "html").page_count = 1;
    },
    /invalid page count/,
  ],
  [
    "PDF page count",
    (d) => {
      findRequired(d.sources, (s) => s.format === "pdf").page_count = 0;
    },
    /invalid page count/,
  ],
  [
    "unused source",
    (d) => {
      d.sources.push({ ...d.sources[0], id: "unused" });
    },
    /unused source metadata/,
  ],
];
runDamageCases(cases);
