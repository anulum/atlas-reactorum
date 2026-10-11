// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — standard source-bound taxonomy release entry point.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const reader = require("../04_interactive_presentation/taxonomy-reviewed-profiles.js");
const {
  exportTaxonomy,
} = require("../04_interactive_presentation/scripts/export_taxonomy.cjs");
const root = path.resolve(__dirname, "..");
const fixture = loadAuthorReviewFixture(root);
const data = "04_interactive_presentation/data";
const reviews = "metadata/evidence_profiles/author_reviews.json";
const products = [
  "taxonomy-expanded.sources.tsv",
  "taxonomy-audit.json",
  "taxonomy-audit.js",
  "taxonomy-evidence-profiles.json",
  "taxonomy-evidence-profiles.js",
  "taxonomy-reviewed-profiles.json",
  "taxonomy-reviewed-profiles.js",
];

/**
 * Retain every genuine input and accepted product before invoking the actual CLI.
 * @param {import("node:test").TestContext} context Owning case and cleanup lifecycle.
 * @returns {string} Independent complete export root with a maintained author input.
 */
function candidate(context) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "atlas-default-review-"));
  context.after(() => fs.rmSync(dir, { recursive: true }));
  for (const relative of [
    "metadata/taxonomy_audit/claim_citations.json",
    "metadata/taxonomy_audit/audit.tsv",
    "metadata/evidence_profiles/profiles.json",
    reviews,
    `${data}/taxonomy-expanded.js`,
    ...products.map((name) => `${data}/${name}`),
  ]) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, relative), target);
  }
  return dir;
}

/**
 * Execute the standard producer from an unrelated working directory.
 * @param {string} dir Explicit complete candidate root.
 * @param {string[]} [selectors] Explicit extra CLI selectors.
 * @returns {import("node:child_process").SpawnSyncReturns<string>} Real native output and exit status.
 */
function exportCli(dir, selectors = []) {
  const env = { ...process.env };
  delete env.ATLAS_AUTHOR_REVIEW_INPUT;
  return spawnSync(
    process.execPath,
    [
      path.join(
        root,
        "04_interactive_presentation/scripts/export_taxonomy.cjs",
      ),
      "--root",
      dir,
      ...selectors,
    ],
    { cwd: os.tmpdir(), env, encoding: "utf8", timeout: 45000 },
  );
}

/**
 * Freeze all seven accepted product bytes for refusal and source-preservation checks.
 * @param {string} dir Full actual candidate.
 * @returns {Buffer[]} Product bytes in the declared original/current order.
 */
function productBytes(dir) {
  return products.map((name) => fs.readFileSync(path.join(dir, data, name)));
}

test("standard CLI recreates both reviewed products from the selected root without a workbench selector", (context) => {
  const dir = candidate(context);
  const before = productBytes(dir);
  const source = fs.readFileSync(path.join(dir, reviews));
  for (const name of products.slice(5))
    fs.unlinkSync(path.join(dir, data, name));
  const result = exportCli(dir);
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(productBytes(dir), before);
  assert.deepEqual(fs.readFileSync(path.join(dir, reviews)), source);
  const inputs = {
    ...fixture.baseline.inputs,
    original_profiles_sha256: createHash("sha256")
      .update(
        fs.readFileSync(
          path.join(dir, "metadata/evidence_profiles/profiles.json"),
        ),
      )
      .digest("hex"),
    author_reviews_sha256: createHash("sha256").update(source).digest("hex"),
  };
  const document = reader.read(
    JSON.parse(fs.readFileSync(path.join(dir, data, products[5]), "utf8")),
    inputs,
    fixture.baseline,
  );
  assert.equal(document.records.length, 135);
  assert.deepEqual(document.author_reviews, fixture.review);
  assert.deepEqual(document.original_profiles, fixture.baseline);
});

for (const fault of ["absent", "stale-binding", "damaged-last-entry"]) {
  test(
    "standard CLI refuses " + fault + " before replacing any accepted product",
    (context) => {
      const dir = candidate(context);
      const before = productBytes(dir);
      const file = path.join(dir, reviews);
      if (fault === "absent") fs.unlinkSync(file);
      else {
        const changed = structuredClone(fixture.review);
        if (fault === "stale-binding")
          changed.baseline_inputs.audit_sha256 = "0".repeat(64);
        else {
          const last = changed.records.at(-1);
          assert.ok(last);
          last.fields.principle.original_value = "changed final source context";
        }
        fs.writeFileSync(file, JSON.stringify(changed));
      }
      const result = exportCli(dir);
      assert.equal(result.status, 1);
      assert.equal(result.stderr, "Taxonomy export refused.\n");
      assert.equal(result.stdout, "");
      assert.deepEqual(productBytes(dir), before);
    },
  );
}

test("explicit complete author input can replace an absent default without changing its source bytes", (context) => {
  const dir = candidate(context);
  const before = productBytes(dir);
  const selected = path.join(dir, "selected-author.json");
  fs.copyFileSync(path.join(dir, reviews), selected);
  const source = fs.readFileSync(selected);
  fs.unlinkSync(path.join(dir, reviews));
  const result = exportCli(dir, ["--reviews", selected]);
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(productBytes(dir), before);
  assert.deepEqual(fs.readFileSync(selected), source);
  assert.equal(fs.existsSync(path.join(dir, reviews)), false);
});

test("unavailable explicitly selected Python refuses before any old or new product is published", (context) => {
  const dir = candidate(context);
  const before = productBytes(dir);
  const previous = process.env.ATLAS_PYTHON;
  process.env.ATLAS_PYTHON = path.join(dir, "nonexistent-python");
  try {
    assert.throws(
      () => exportTaxonomy(dir, path.join(dir, reviews)),
      /complete snapshot validation failed/,
    );
    const result = exportCli(dir);
    assert.equal(result.status, 1);
    assert.equal(result.stderr, "Taxonomy export refused.\n");
    assert.equal(result.stdout, "");
    assert.deepEqual(productBytes(dir), before);
  } finally {
    if (previous === undefined) delete process.env.ATLAS_PYTHON;
    else process.env.ATLAS_PYTHON = previous;
  }
});
