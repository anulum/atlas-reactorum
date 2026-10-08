// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — binding citation contracts.
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

test("resolve every actual citation without approving any complete entry or mutating source data", () => {
  const before = JSON.stringify(rows);
  const result = readCitations(root, rows);
  assert.equal(result.size, 135);
  assert.deepEqual(
    [...result.keys()],
    rows.map((row) => row.id),
  );
  assert.equal(
    [...result.values()].filter((citations) => citations.length).length,
    135,
  );
  assert.equal([...result.values()].flat().length, 599);
  assert.equal(JSON.stringify(rows), before);
  for (const record of original.records) {
    assert.equal(record.complete_entry_review, false);
    const citations = getRequired(result, record.id);
    for (const [index, citation] of record.citations.entries()) {
      const source = findRequired(
        original.sources,
        (item) => item.id === citation.source_id,
      );
      assert.deepEqual(citations[index], {
        ...citation,
        source_title: source.title,
        source_url: source.url,
        source_sha256: source.sha256,
        source_capture_method: source.capture_method,
        source_captured_at: source.captured_at,
      });
    }
  }
  assert.deepEqual(
    getRequired(result, "subcritical-assembly")[0].pdf_pages,
    [13],
  );
  assert.deepEqual(
    getRequired(result, "subcritical-assembly")[0].printed_pages,
    ["3"],
  );
  assert.match(
    getRequired(result, "subcritical-assembly")[0].scope,
    /not a claim that every assembly/,
  );
});

test("physical claims bind the complete actual field and distinguish retained NRC originals from publisher captures", () => {
  const result = readCitations(root, rows);
  const physical = [...result.values()]
    .flat()
    .filter((citation) =>
      ["principle", "strength", "challenge"].includes(citation.topic),
    );
  assert.equal(physical.length, 480);
  for (const row of rows) {
    for (const citation of getRequired(result, row.id).filter((item) =>
      ["principle", "strength", "challenge"].includes(item.topic),
    )) {
      assert.equal(citation.statement, physicalField(row, citation.topic));
      assert.ok(row.source_urls.includes(citation.source_url));
    }
  }
  const retained = physical.filter(
    (citation) => citation.source_capture_method === "retained-source-review",
  );
  assert.equal(retained.length, 146);
  assert.ok(retained.every((citation) => citation.source_captured_at === null));
  const nrc = retained.filter(
    (citation) =>
      citation.source_title.startsWith("NRC") ||
      citation.source_title.startsWith("Reactor Concepts Manual"),
  );
  assert.equal(nrc.length, 7);
  assert.ok(nrc.every((citation) => citation.source_captured_at === null));
  const pwr = findRequired(
    getRequired(result, "pwr"),
    (citation) => citation.topic === "principle",
  );
  assert.deepEqual(pwr.pdf_pages, [75, 76]);
  assert.deepEqual(pwr.printed_pages, ["75", "76"]);
  const bwr = getRequired(result, "bwr").filter(
    (citation) => citation.topic === "principle",
  );
  assert.deepEqual(
    bwr.map((citation) => citation.pdf_pages),
    [[21], [2]],
  );
  assert.deepEqual(
    bwr.map((citation) => citation.printed_pages),
    [["21"], ["3-2"]],
  );
  const integral = findRequired(
    getRequired(result, "integral-pwr"),
    (citation) => citation.topic === "principle",
  );
  assert.match(integral.statement, /^Most or all primary system components/);
  assert.equal(integral.source_capture_method, "publisher-tls");
  assert.deepEqual(integral.pdf_pages, [20, 146]);
  assert.match(integral.scope, /educational evidence/);
});
