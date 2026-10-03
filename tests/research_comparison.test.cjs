// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native research import public contract tests
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { restore, run } = require("../04_interactive_presentation/scripts/research_comparison.cjs");
const root = path.resolve(__dirname, "..");
const input = path.join(root, "metadata/evidence_profiles/profiles.json");
const document = JSON.parse(fs.readFileSync(input, "utf8"));
const snapshot = createHash("sha256").update(JSON.stringify(document)).digest("hex");
const digest = text => createHash("sha256").update(text, "utf8").digest("hex");
const serialize = value => JSON.stringify(value, null, 2) + "\n";

async function bundle(ids = ["pwr", "bwr"]) {
  return globalThis.AtlasTaxonomyComparison.createComparison(document, snapshot, ids);
}

async function withFile(text, action) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "atlas-research-"));
  try {
    const file = path.join(dir, "comparison.json");
    fs.writeFileSync(file, text);
    return await action(file);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test("all135 real stable identities round-trip with exact original claims, sources and display order", async () => {
  for (const record of document.records) {
    const ids = [record.entry_id, record.entry_id === "pwr" ? "bwr" : "pwr"];
    const expected = await bundle(ids);
    const text = serialize(expected);
    assert.deepEqual(await restore(document, snapshot, text, digest(text)), expected);
    assert.deepEqual(expected.profiles, ids.map(id => document.records.find(row => row.entry_id === id)));
  }
});

test("native export and restore share the real public model for two and three selected identities", async () => {
  for (const ids of [["pwr", "bwr"], ["tokamak", "pwr", "bwr"]]) {
    const expected = await bundle(ids);
    assert.deepEqual(await run(["--export", input, snapshot, ...ids]), expected);
    const text = serialize(expected);
    await withFile(text, async file => assert.deepEqual(
      await run(["--restore", input, snapshot, file, digest(text)]), expected));
  }
});

for (const args of [[], ["--unknown"], ["--export", input, snapshot, "pwr"],
  ["--export", input, snapshot, "pwr", "bwr", "tokamak", "cstr"],
  ["--restore", input, snapshot, "file", "a".repeat(64), "extra"]]) {
  test("invalid native mode/selection arguments refuse: " + JSON.stringify(args), async () => {
    await assert.rejects(run(args));
  });
}

test("stale whole-profile snapshots, changed unselected profiles and invalid selected identity refuse", async () => {
  const text = serialize(await bundle());
  await assert.rejects(restore(document, "0".repeat(64), text, digest(text)));
  const changed = structuredClone(document); changed.records.at(-1).parameters[0].reason += " changed";
  await assert.rejects(restore(changed, snapshot, text, digest(text)));
  const unknown = await bundle(); unknown.selection.entry_ids[1] = "nonexistent";
  const bad = serialize(unknown); await assert.rejects(restore(document, snapshot, bad, digest(bad)));
});

for (const value of ["not-a-hash", "A".repeat(64), "0".repeat(64)]) {
  test("malformed or changed original-export digest refuses: " + value, async () => {
    const text = serialize(await bundle()); await assert.rejects(restore(document, snapshot, text, value));
  });
}

for (const edit of [
  value => { value.profiles[0].claims[0].original_statement += " changed"; },
  value => { value.sources[0].url = "https://example.org/changed"; },
  value => { value.source_rights = "invented redistribution"; },
  value => { value.selection.entry_ids.reverse(); },
  value => { value.parameter_comparisons[0].state = "same_declared_context"; },
  value => { value.extra = true; },
  value => { value.snapshot.inputs.taxonomy_sha256 = "0".repeat(64); },
]) {
  test("even a newly supplied file digest cannot promote changed original comparison content: " + edit.toString(), async () => {
    const value = await bundle(); edit(value); const text = serialize(value);
    await assert.rejects(restore(document, snapshot, text, digest(text)));
  });
}

for (const transform of [
  text => text.trimEnd(), text => text.replace('"schema_version":', '"schema_version": "wrong", "schema_version":'),
  text => text.replace('"complete_entry_review": false', '"complete_entry_review": NaN'),
  () => "not JSON\n", () => "null\n",
]) {
  test("noncanonical, duplicate, nonfinite, malformed and empty original files refuse: " + transform.toString(), async () => {
    const text = transform(serialize(await bundle())); await assert.rejects(restore(document, snapshot, text, digest(text)));
  });
}

test("actual native CLI succeeds with canonical output and refuses missing/invalid inputs with safe fixed stderr", async () => {
  const script = path.join(root, "04_interactive_presentation/scripts/research_comparison.cjs");
  const success = spawnSync(process.execPath, [script, "--export", input, snapshot, "pwr", "bwr"], { encoding: "utf8" });
  assert.equal(success.status, 0); assert.equal(success.stderr, ""); assert.equal(success.stdout, serialize(await bundle()));
  const stdin = spawnSync(process.execPath, [script], { encoding: "utf8",
    input: JSON.stringify(["--export", input, snapshot, "pwr", "bwr"]) });
  assert.equal(stdin.status, 0); assert.equal(stdin.stdout, success.stdout);
  for (const request of ["{", "null", JSON.stringify(["--unknown"])]) {
    const refused = spawnSync(process.execPath, [script], { encoding: "utf8", input: request });
    assert.equal(refused.status, 2); assert.equal(refused.stdout, "");
    assert.equal(refused.stderr, "research comparison: input or source binding refused\n");
  }
  await withFile(success.stdout, async file => {
    const result = spawnSync(process.execPath, [script, "--restore", input, snapshot, file, digest(success.stdout)], { encoding: "utf8" });
    assert.equal(result.status, 0); assert.equal(result.stdout, success.stdout);
    fs.writeFileSync(file, Buffer.from([0xff, 0xfe]));
    await assert.rejects(run(["--restore", input, snapshot, file, digest(success.stdout)]));
  });
  for (const args of [[], ["--export", input + ".missing", snapshot, "pwr", "bwr"],
    ["--restore", input, snapshot, input + ".missing", "a".repeat(64)]]) {
    const failure = spawnSync(process.execPath, [script, ...args], { encoding: "utf8" });
    assert.equal(failure.status, 2); assert.equal(failure.stdout, "");
    assert.equal(failure.stderr, "research comparison: input or source binding refused\n");
  }
});
