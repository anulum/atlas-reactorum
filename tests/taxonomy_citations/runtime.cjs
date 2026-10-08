// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — runtime citation contracts.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {
  readCitations,
} = require("../../04_interactive_presentation/scripts/taxonomy_citations.cjs");
const { loadFixture } = require("../taxonomy_citation_fixture.cjs");
const root = path.resolve(__dirname, "../..");
const { rows } = loadFixture(root);
const input = "metadata/taxonomy_audit/claim_citations.json";

test("reject missing metadata, malformed JSON, missing taxonomy and invalid runtime catalogue", (context) => {
  const dir = fs.mkdtempSync(
    path.join(
      process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(),
      "atlas-citations-",
    ),
  );
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
  assert.throws(
    () => readCitations(root, duplicates),
    /identity or order mismatch/,
  );
});

for (const invalidEntry of [null, [], 1]) {
  test(
    "refuse an invalid runtime entry: " + JSON.stringify(invalidEntry),
    () => {
      const damaged = structuredClone(rows);
      assert.ok(Reflect.set(damaged, 0, invalidEntry));
      assert.throws(
        () => readCitations(root, damaged),
        /Taxonomy entry: expected an object/,
      );
    },
  );
}
