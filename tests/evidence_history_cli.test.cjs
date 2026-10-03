// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — real history imports, review files and transactional presentation builds
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const { spawnSync } = require("node:child_process");
const { build, run } = require("../04_interactive_presentation/scripts/evidence_history.cjs");
const historyApi = globalThis.AtlasEvidenceHistory;
const script = path.join(__dirname, "../04_interactive_presentation/scripts/evidence_history.cjs");
const document = JSON.parse(fs.readFileSync(path.join(__dirname, "../04_interactive_presentation/data/taxonomy-evidence-profiles.json"), "utf8"));
const time = "2026-10-03T07:20:00.000Z";
const nextTime = "2026-10-04T07:20:00.000Z";
const serialise = value => JSON.stringify(value, null, 2) + "\n";
function directory(context) {
  const temporary = fs.mkdtempSync(path.join(process.env.ATLAS_TEST_WORKSPACE || os.tmpdir(), "atlas-evidence-history-"));
  context.after(() => fs.rmSync(temporary, { recursive: true }));
  return temporary;
}
function cli(...args) {
  return spawnSync(process.execPath, [script, ...args], { cwd: os.tmpdir(), encoding: "utf8", timeout: 20000, maxBuffer: 2 * 1024 * 1024 });
}
async function candidate(context) {
  const root = directory(context);
  const history = await historyApi.importProfiles(null, document, time);
  fs.mkdirSync(path.join(root, "metadata/evidence_history"), { recursive: true });
  fs.mkdirSync(path.join(root, "04_interactive_presentation/data"), { recursive: true });
  fs.writeFileSync(path.join(root, "metadata/evidence_history/history.json"), serialise(history));
  fs.writeFileSync(path.join(root, "04_interactive_presentation/data/taxonomy-evidence-profiles.json"), serialise(document));
  return { root, history };
}

test("actual initialise/import commands preserve original input files and repeat unchanged source idempotently", async context => {
  const root = directory(context);
  const profile = path.join(root, "profiles.json"); fs.writeFileSync(profile, serialise(document));
  const history = path.join(root, "history.json");
  const initial = cli("--initialise", profile, time, history);
  assert.equal(initial.status, 0, initial.stderr);
  assert.deepEqual(JSON.parse(initial.stdout), { snapshots: 1, observations: 1 });
  const original = fs.readFileSync(history);
  const repeated = path.join(root, "repeated.json");
  const repeat = cli("--import", history, profile, nextTime, repeated);
  assert.equal(repeat.status, 0, repeat.stderr);
  assert.deepEqual(fs.readFileSync(repeated), original);
  const changed = structuredClone(document);
  changed.records[0].claims[0].original_statement += " Controlled input correction.";
  changed.records[0].claims[0].citation.statement = changed.records[0].claims[0].original_statement;
  const newProfile = path.join(root, "changed-profiles.json"); fs.writeFileSync(newProfile, serialise(changed));
  const revised = path.join(root, "revised.json");
  const update = cli("--import", history, newProfile, nextTime, revised);
  assert.equal(update.status, 0, update.stderr);
  assert.deepEqual(JSON.parse(update.stdout), { snapshots: 2, observations: 2 });
  const next = JSON.parse(fs.readFileSync(revised, "utf8"));
  assert.deepEqual(next.snapshots[0].document, document);
  assert.deepEqual(next.snapshots[1].document, changed);
  assert.deepEqual(fs.readFileSync(history), original);
  assert.equal(fs.readFileSync(profile, "utf8"), serialise(document));
  assert.equal(fs.readFileSync(newProfile, "utf8"), serialise(changed));
  const exists = cli("--import", history, profile, nextTime, history);
  assert.equal(exists.status, 2);
  assert.deepEqual(fs.readFileSync(history), original);
});

test("public explicit mode API and actual CLI rebuild identical journal products without changing retained inputs", async context => {
  const { root, history } = await candidate(context);
  const before = fs.readFileSync(path.join(root, "metadata/evidence_history/history.json"));
  assert.deepEqual(await run(["--build", root]), { snapshots: 1, observations: 1 });
  const jsonFile = path.join(root, "04_interactive_presentation/data/evidence-history.json");
  const jsFile = path.join(root, "04_interactive_presentation/data/evidence-history.js");
  const json = fs.readFileSync(jsonFile); const js = fs.readFileSync(jsFile);
  assert.deepEqual(JSON.parse(json), history);
  const window = {};
  vm.runInNewContext(js.toString(), { window });
  assert.deepEqual(JSON.parse(JSON.stringify(window.REACTOR_EVIDENCE_HISTORY)), history);
  const result = cli("--build", root);
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(fs.readFileSync(jsonFile), json);
  assert.deepEqual(fs.readFileSync(jsFile), js);
  assert.deepEqual(fs.readFileSync(path.join(root, "metadata/evidence_history/history.json")), before);
  assert.equal(fs.readdirSync(path.dirname(jsonFile)).some(name => name.startsWith(".history-build-")), false);
});

test("current source change cannot silently overwrite the last explicitly recorded journal version", async context => {
  const { root } = await candidate(context);
  await build(root);
  const data = path.join(root, "04_interactive_presentation/data");
  const before = ["evidence-history.json", "evidence-history.js"].map(name => fs.readFileSync(path.join(data, name)));
  const changed = structuredClone(document); changed.records.at(-1).parameters[0].reason += " Later controlled input.";
  fs.writeFileSync(path.join(data, "taxonomy-evidence-profiles.json"), serialise(changed));
  await assert.rejects(build(root), /last explicitly imported/);
  const result = cli("--build", root);
  assert.equal(result.status, 2);
  for (const [index, name] of ["evidence-history.json", "evidence-history.js"].entries()) {
    assert.deepEqual(fs.readFileSync(path.join(data, name)), before[index]);
  }
});

for (const originals of [true, false]) {
  test(`real output I/O refusal rolls back previously published history products (original ${originals})`, async context => {
    const { root } = await candidate(context);
    const data = path.join(root, "04_interactive_presentation/data");
    const jsonFile = path.join(data, "evidence-history.json");
    const jsFile = path.join(data, "evidence-history.js");
    if (originals) await build(root);
    const before = originals ? fs.readFileSync(jsonFile) : null;
    if (originals) fs.unlinkSync(jsFile);
    fs.mkdirSync(jsFile);
    await assert.rejects(build(root), /EISDIR/);
    if (originals) assert.deepEqual(fs.readFileSync(jsonFile), before);
    else assert.equal(fs.existsSync(jsonFile), false);
    assert.equal(fs.statSync(jsFile).isDirectory(), true);
    assert.equal(fs.readdirSync(data).some(name => name.startsWith(".history-build-")), false);
  });
}

test("actual curator commands record both decisions without applying or mutating original proposals/history", async context => {
  const { root, history } = await candidate(context);
  const digest = await historyApi.digest(history);
  const revision = (await historyApi.readClaim(history, digest, "pwr", "pwr:classification:1")).revisions[0];
  const proposal = await globalThis.AtlasEvidenceCorrections.propose(history, digest, "pwr", "pwr:classification:1", revision.revision_sha256,
    { proposed_statement: "A controlled narrower classification proposal.", source_url: revision.source.url,
      locator: revision.claim.citation.section, reason: "Clarify its scope.", submitted_by: "Named contributor", proposed_at: time });
  const pending = path.join(root, "pending.json"); fs.writeFileSync(pending, serialise(proposal));
  const pendingBefore = fs.readFileSync(pending);
  const historyBefore = fs.readFileSync(path.join(root, "metadata/evidence_history/history.json"));
  for (const decision of ["accepted-for-editing", "rejected"]) {
    const review = { decision, reviewed_by: "Named curator", reviewed_at: nextTime,
      reason: "The source locator was inspected.", source_url: revision.source.url, locator: revision.claim.citation.section };
    const input = path.join(root, decision + "-review.json"); fs.writeFileSync(input, serialise(review));
    const output = path.join(root, decision + ".json");
    const actual = cli("--review", pending, input, output);
    assert.equal(actual.status, 0, actual.stderr);
    assert.equal(JSON.parse(actual.stdout).state, decision);
    const reviewed = JSON.parse(fs.readFileSync(output, "utf8"));
    assert.deepEqual(reviewed.original_revision, revision);
    assert.deepEqual(reviewed.review, review);
    assert.equal(reviewed.publication_effect, "none; accepted source data remain unchanged");
    const refused = cli("--review", pending, input, output);
    assert.equal(refused.status, 2);
  }
  assert.deepEqual(fs.readFileSync(pending), pendingBefore);
  assert.deepEqual(fs.readFileSync(path.join(root, "metadata/evidence_history/history.json")), historyBefore);
  const freshPending = path.join(root, "fresh-pending.json");
  await run(["--initialise", path.join(root, "04_interactive_presentation/data/taxonomy-evidence-profiles.json"), time, freshPending]);
  const bad = cli("--review", freshPending, freshPending, path.join(root, "bad-review.json"));
  assert.equal(bad.status, 2);
  assert.equal(fs.existsSync(path.join(root, "bad-review.json")), false);
});

test("public mode API refuses invalid args and actual native caller text never echoes exceptions or source input", async context => {
  const root = directory(context);
  for (const args of [[], ["--unknown"], ["--initialise"], ["--import"], ["--review"], ["--build", root, "extra"],
    ["--initialise", path.join(root, "missing-sensitive-input.json"), time, path.join(root, "missing.json")]]) {
    await assert.rejects(run(args));
    const result = cli(...args);
    assert.equal(result.status, 2);
    assert.equal(result.stdout, "");
    assert.equal(result.stderr, "Evidence history command refused: its inputs, dates, output paths or retained source content are unavailable or invalid.\n");
  }
});

test("noncanonical, duplicate-key and malformed JSON refuse before any new output is created", async context => {
  const root = directory(context);
  const input = path.join(root, "input.json"); const output = path.join(root, "output.json");
  for (const raw of ["{invalid}", JSON.stringify(document), serialise(document).replace('"schema_version": "1.0.0",', '"schema_version": "future",\n  "schema_version": "1.0.0",')]) {
    fs.writeFileSync(input, raw);
    const result = cli("--initialise", input, time, output);
    assert.equal(result.status, 2);
    assert.equal(fs.existsSync(output), false);
    assert.equal(fs.readFileSync(input, "utf8"), raw);
  }
});
