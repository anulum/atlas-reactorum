// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — whole reviewed export and source-preserving consumer conformance.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const vm = require("node:vm");
const { createHash } = require("node:crypto");
const { spawnSync } = require("node:child_process");
const {
  exportTaxonomy,
} = require("../04_interactive_presentation/scripts/export_taxonomy.cjs");
const reader = require("../04_interactive_presentation/taxonomy-reviewed-profiles.js");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const root = path.resolve(__dirname, "..");
const fixture = loadAuthorReviewFixture(root);
const data = "04_interactive_presentation/data";
const originalProducts = [
  "taxonomy-expanded.sources.tsv",
  "taxonomy-audit.json",
  "taxonomy-audit.js",
  "taxonomy-evidence-profiles.json",
  "taxonomy-evidence-profiles.js",
];
/**
 * Copy actual sources/products into a newly owned independent export root.
 * @param {import("node:test").TestContext} context Actual case lifecycle.
 * @returns {string} Complete native candidate with genuine whole author input.
 */
function candidate(context) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "atlas-reviewed-export-"));
  context.after(() => fs.rmSync(dir, { recursive: true }));
  for (const relative of [
    "metadata/taxonomy_audit/claim_citations.json",
    "metadata/taxonomy_audit/audit.tsv",
    "metadata/evidence_profiles/profiles.json",
    `${data}/taxonomy-expanded.js`,
    ...originalProducts.map((name) => `${data}/${name}`),
  ]) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, relative), target);
  }
  const source =
    process.env.ATLAS_AUTHOR_REVIEW_INPUT ||
    path.join(root, "metadata/evidence_profiles/author_reviews.json");
  fs.copyFileSync(
    source,
    path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
  );
  return dir;
}
/**
 * Observe every original export without deriving a baseline from new products.
 * @param {string} dir Actual complete source/export root.
 * @returns {Buffer[]} Exact independently retained original product bytes.
 */
function originalBytes(dir) {
  return originalProducts.map((name) =>
    fs.readFileSync(path.join(dir, data, name)),
  );
}
/**
 * Load an actual successfully produced reviewed document for consumer mutations.
 * @param {string} dir Complete actual export root.
 * @returns {import("../04_interactive_presentation/scripts/taxonomy_reviewed_products.cjs").ReviewedProfileDocument} Genuine producer output, admitted before any mutation.
 */
function product(dir) {
  exportTaxonomy(
    dir,
    path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
  );
  /** @type {unknown} */
  const raw = JSON.parse(
    fs.readFileSync(
      path.join(dir, data, "taxonomy-reviewed-profiles.json"),
      "utf8",
    ),
  );
  const inputs = {
    ...fixture.baseline.inputs,
    original_profiles_sha256: createHash("sha256")
      .update(
        fs.readFileSync(
          path.join(dir, "metadata/evidence_profiles/profiles.json"),
        ),
      )
      .digest("hex"),
    author_reviews_sha256: createHash("sha256")
      .update(
        fs.readFileSync(
          path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
        ),
      )
      .digest("hex"),
  };
  return reader.read(raw, inputs, fixture.baseline);
}
test("the real export keeps all original artifacts and emits identical complete reviewed JSON/classic products", (context) => {
  const dir = candidate(context),
    before = originalBytes(dir);
  const document = product(dir);
  assert.deepEqual(originalBytes(dir), before);
  assert.equal(document.records.length, 135);
  assert.deepEqual(document.original_profiles, fixture.baseline);
  assert.deepEqual(document.author_reviews, fixture.review);
  const host = {
    REACTOR_TAXONOMY_REVIEWED_PROFILES: /** @type {unknown} */ (undefined),
    REACTOR_TAXONOMY_REVIEWED_PROFILE_INPUTS: /** @type {unknown} */ (
      undefined
    ),
  };
  vm.runInNewContext(
    fs.readFileSync(
      path.join(dir, data, "taxonomy-reviewed-profiles.js"),
      "utf8",
    ),
    { window: host },
  );
  assert.deepEqual(
    structuredClone(host.REACTOR_TAXONOMY_REVIEWED_PROFILES),
    document,
  );
  assert.deepEqual(
    structuredClone(host.REACTOR_TAXONOMY_REVIEWED_PROFILE_INPUTS),
    document.inputs,
  );
  assert.ok(Object.isFrozen(host.REACTOR_TAXONOMY_REVIEWED_PROFILE_INPUTS));
  const selected = reader.readProfile(
    document,
    document.inputs,
    fixture.baseline,
    "phwr-candu",
  );
  assert.equal(
    selected.taxonomy_record.name,
    "Pressure-tube PHWR including CANDU",
  );
  assert.equal(selected.original_profile.taxonomy_record.name, "PHWR / CANDU");
  selected.author_review.fields.name.assessment = "caller mutation";
  assert.deepEqual(document.author_reviews, fixture.review);
  assert.throws(() =>
    reader.readProfile(
      document,
      document.inputs,
      fixture.baseline,
      "absent-entry",
    ),
  );
  const first = fs.readFileSync(
    path.join(dir, data, "taxonomy-reviewed-profiles.json"),
  );
  exportTaxonomy(
    dir,
    path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
  );
  assert.deepEqual(
    fs.readFileSync(path.join(dir, data, "taxonomy-reviewed-profiles.json")),
    first,
  );
});
test("an invalid last author entry refuses before changing any original product", (context) => {
  const dir = candidate(context),
    before = originalBytes(dir),
    source = path.join(dir, "metadata/evidence_profiles/author_reviews.json");
  const doc = structuredClone(fixture.review),
    last = doc.records.at(-1);
  assert.ok(last);
  last.fields.principle.original_value = "changed last original";
  fs.writeFileSync(source, JSON.stringify(doc));
  assert.throws(() => exportTaxonomy(dir, source), /complete author admission/);
  assert.deepEqual(originalBytes(dir), before);
  assert.ok(
    !fs.existsSync(path.join(dir, data, "taxonomy-reviewed-profiles.json")),
  );
});
test("real final reviewed-script I/O failure restores all five originals and removes the newly published JSON", (context) => {
  const dir = candidate(context),
    before = originalBytes(dir);
  fs.mkdirSync(path.join(dir, data, "taxonomy-reviewed-profiles.js"));
  assert.throws(
    () =>
      exportTaxonomy(
        dir,
        path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
      ),
    /EISDIR/,
  );
  assert.deepEqual(originalBytes(dir), before);
  assert.ok(
    !fs.existsSync(path.join(dir, data, "taxonomy-reviewed-profiles.json")),
  );
});
test("a review input stored at an output path is protected before product replacement", (context) => {
  const dir = candidate(context),
    source = path.join(dir, data, "taxonomy-reviewed-profiles.json");
  fs.copyFileSync(
    path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
    source,
  );
  const bytes = fs.readFileSync(source),
    before = originalBytes(dir);
  assert.throws(
    () => exportTaxonomy(dir, source),
    /cannot replace author input/,
  );
  assert.deepEqual(fs.readFileSync(source), bytes);
  assert.deepEqual(originalBytes(dir), before);
});
test("the extended public CLI accepts explicit reviews and refuses duplicate/missing selectors", (context) => {
  const dir = candidate(context),
    script = path.join(
      root,
      "04_interactive_presentation/scripts/export_taxonomy.cjs",
    ),
    source = path.join(dir, "metadata/evidence_profiles/author_reviews.json");
  const result = spawnSync(
    process.execPath,
    [script, "--root", dir, "--reviews", source],
    { encoding: "utf8", timeout: 45000 },
  );
  assert.equal(result.status, 0, result.stderr);
  for (const args of [
    ["--reviews"],
    ["--root", dir, "--root", dir],
    ["--reviews", "--root", dir],
  ]) {
    const result = spawnSync(process.execPath, [script, ...args], {
      encoding: "utf8",
      timeout: 45000,
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Usage: export_taxonomy/);
  }
});

test("the actual reviewed export also uses its default Python selector", (context) => {
  const dir = candidate(context),
    environment = { ...process.env };
  delete environment.ATLAS_PYTHON;
  const result = spawnSync(
    process.execPath,
    [
      path.join(
        root,
        "04_interactive_presentation/scripts/export_taxonomy.cjs",
      ),
      "--root",
      dir,
      "--reviews",
      path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
    ],
    { env: environment, encoding: "utf8", timeout: 45000 },
  );
  assert.equal(result.status, 0, result.stderr);
  assert.ok(
    fs.existsSync(path.join(dir, data, "taxonomy-reviewed-profiles.json")),
  );
});
for (const fault of [
  "version",
  "count",
  "rights",
  "license",
  "hash",
  "original",
  "original-object",
  "original-scalar",
  "original-array",
  "original-key",
  "current",
  "current-array",
  "current-length",
  "author",
  "extra",
]) {
  test("the entire reviewed consumer refuses " + fault, (context) => {
    const dir = candidate(context),
      actual = product(dir),
      doc = structuredClone(actual);
    if (fault === "version") Object.assign(doc, { schema_version: "unknown" });
    else if (fault === "count") doc.record_count--;
    else if (fault === "rights")
      Object.assign(doc, { source_rights: "unrestricted" });
    else if (fault === "license")
      Object.assign(doc, { metadata_license: "unknown" });
    else if (fault === "hash")
      doc.inputs.author_reviews_sha256 = "0".repeat(64);
    else if (fault === "original")
      doc.original_profiles.records[0].taxonomy_record.name =
        "changed original";
    else if (fault === "original-object")
      Object.assign(doc, { original_profiles: null });
    else if (fault === "original-scalar")
      Object.assign(doc, { original_profiles: 17 });
    else if (fault === "original-array")
      Object.assign(doc, { original_profiles: [] });
    else if (fault === "original-key") {
      const original = /** @type {Record<string,unknown>} */ (
        /** @type {unknown} */ (doc.original_profiles)
      );
      original.replaced = original.schema_version;
      delete original.schema_version;
    } else if (fault === "current")
      doc.records[0].name = "changed unassessed current";
    else if (fault === "current-array") Object.assign(doc, { records: {} });
    else if (fault === "current-length") doc.records.pop();
    else if (fault === "author")
      doc.author_reviews.records[0].fields.principle.original_value =
        "changed original";
    else Object.assign(doc, { extra: true });
    assert.throws(() => reader.read(doc, actual.inputs, fixture.baseline));
  });
}

test("the original classic reader checks explicit source authority and admits the same whole product", (context) => {
  const dir = candidate(context),
    document = product(dir);
  const host = vm.createContext({
    document,
    original: fixture.baseline,
    structuredClone,
  });
  for (const name of [
    "author-review-values.js",
    "author-review-dimensions.js",
    "author-review-revisions.js",
    "taxonomy-author-review.js",
    "taxonomy-reviewed-profiles.js",
  ]) {
    const filename = path.join(root, "04_interactive_presentation", name);
    vm.runInContext(fs.readFileSync(filename, "utf8"), host, { filename });
  }
  assert.equal(
    vm.runInContext(
      "AtlasTaxonomyReviewedProfiles.read(document,document.inputs,original)",
      host,
    ),
    document,
  );
  const changed = structuredClone(document);
  changed.inputs.taxonomy_sha256 = "0".repeat(64);
  assert.throws(
    () => reader.read(changed, changed.inputs, fixture.baseline),
    /source hashes/,
  );
});

for (const source of ["profile", "review", "restored-review"]) {
  test(
    "real composer refuses concurrent " + source + " source changes",
    async (context) => {
      const { Worker } = require("node:worker_threads");
      const { once } = require("node:events");
      const {
        reviewedProducts,
      } = require("../04_interactive_presentation/scripts/taxonomy_reviewed_products.cjs");
      const dir = candidate(context);
      const filename = path.join(
        dir,
        source === "profile"
          ? "metadata/evidence_profiles/profiles.json"
          : "metadata/evidence_profiles/author_reviews.json",
      );
      const before = fs.readFileSync(filename);
      const changed =
        source === "profile"
          ? structuredClone(fixture.baseline)
          : structuredClone(fixture.review);
      if (source === "profile") {
        const parameter =
          /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
            changed
          ).records[0].parameters[0];
        assert.ok(parameter.state !== "known");
        parameter.reason += " Concurrent source context.";
      } else
        /** @type {import("../04_interactive_presentation/taxonomy-author-review.js").AuthorReviewDocument} */ (
          changed
        ).records[0].fields.id.assessment += " Concurrent author context.";
      fs.utimesSync(filename, 0, fs.statSync(filename).mtime);
      const state = new SharedArrayBuffer(4);
      const program = `const {workerData,parentPort}=require('node:worker_threads');const fs=require('node:fs');const wait=new Int32Array(new SharedArrayBuffer(4));const end=Date.now()+45000;while(fs.statSync(workerData.filename).atimeMs===0&&Date.now()<end)Atomics.wait(wait,0,0,1);const temp=workerData.filename+'.replacement';fs.writeFileSync(temp,workerData.changed);if(workerData.restore)fs.utimesSync(temp,0,fs.statSync(temp).mtime);fs.renameSync(temp,workerData.filename);if(workerData.restore){while(fs.statSync(workerData.filename).atimeMs===0&&Date.now()<end)Atomics.wait(wait,0,0,1);fs.writeFileSync(temp,Buffer.from(workerData.before,'base64'));fs.renameSync(temp,workerData.filename);}Atomics.store(new Int32Array(workerData.state),0,1);parentPort.postMessage('done');`;
      const worker = new Worker(program, {
        eval: true,
        workerData: {
          filename,
          changed: JSON.stringify(changed),
          before: before.toString("base64"),
          restore: source === "restored-review",
          state,
        },
      });
      await once(worker, "online");
      try {
        assert.throws(
          () =>
            reviewedProducts(
              dir,
              fixture.baseline.inputs.taxonomy_sha256,
              fixture.baseline,
              path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
            ),
          /source changed during composition/,
        );
        await once(worker, "exit");
        assert.equal(Atomics.load(new Int32Array(state), 0), 1);
        if (source === "restored-review")
          assert.deepEqual(fs.readFileSync(filename), before);
      } finally {
        await worker.terminate();
      }
    },
  );
}

test("real review-input symlink and a separately admitted original cannot replace source custody", (context) => {
  const {
    reviewedProducts,
  } = require("../04_interactive_presentation/scripts/taxonomy_reviewed_products.cjs");
  const dir = candidate(context),
    source = path.join(dir, "metadata/evidence_profiles/author_reviews.json"),
    target = path.join(dir, data, "taxonomy-reviewed-profiles.json"),
    alias = path.join(dir, "source-alias.json");
  fs.copyFileSync(source, target);
  fs.symlinkSync(target, alias);
  assert.throws(
    () => exportTaxonomy(dir, alias),
    /cannot replace author input/,
  );
  const other = candidate(context),
    profile = path.join(other, "metadata/evidence_profiles/profiles.json");
  const changed = structuredClone(fixture.baseline);
  const parameter = changed.records[0].parameters[0];
  assert.ok(parameter.state !== "known");
  parameter.reason += " Separately admitted metadata.";
  fs.writeFileSync(profile, JSON.stringify(changed));
  const validated = spawnSync(
    process.env.ATLAS_PYTHON || "python3",
    [
      path.join(root, "metadata/evidence_profiles/validate.py"),
      "--root",
      other,
      "--snapshot",
      fixture.baseline.inputs.taxonomy_sha256,
    ],
    { encoding: "utf8", timeout: 45000, maxBuffer: 8 * 1024 * 1024 },
  );
  assert.equal(validated.status, 0, validated.stderr);
  const admitted =
    /** @type {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
      JSON.parse(validated.stdout)
    );
  assert.throws(
    () =>
      reviewedProducts(
        dir,
        fixture.baseline.inputs.taxonomy_sha256,
        admitted,
        source,
      ),
    /source changed during composition/,
  );
});
