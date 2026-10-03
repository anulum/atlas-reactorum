// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — explicit history imports, curator records and offline presentation build
"use strict";

const fs = require("node:fs");
const path = require("node:path");
require("../taxonomy-claim-sources.js");
require("../taxonomy-evidence-profile.js");
require("../taxonomy-comparison.js");
require("../evidence-history.js");
require("../evidence-corrections.js");

const serialise = value => JSON.stringify(value, null, 2) + "\n";
function read(file) {
  const raw = fs.readFileSync(file, "utf8");
  const value = JSON.parse(raw);
  // The journal's on-disk contract has one canonical representation. This
  // also refuses duplicate JSON keys and lossy nonfinite numeric literals.
  if (serialise(value) !== raw) throw new Error("History input needs canonical two-space JSON and a final newline");
  return value;
}

function writeNew(file, value) {
  fs.writeFileSync(file, serialise(value), { flag: "wx" });
}

/**
 * Rebuild the two presentation history products from a retained input journal.
 * @param {string} repositoryRoot Complete candidate including current accepted profiles.
 * @returns {Promise<object>} Validated snapshot and observation counts; no acquisition occurs.
 * @throws {Error} If the accepted profiles differ or input/output custody is unavailable.
 */
async function build(repositoryRoot) {
  const root = path.resolve(repositoryRoot);
  const history = read(path.join(root, "metadata/evidence_history/history.json"));
  await globalThis.AtlasEvidenceHistory.validate(history);
  const profiles = read(path.join(root, "04_interactive_presentation/data/taxonomy-evidence-profiles.json"));
  if (await globalThis.AtlasTaxonomyComparison.snapshot(profiles) !== history.imports.at(-1).profile_sha256) {
    throw new Error("Current profiles differ from the last explicitly imported history snapshot");
  }
  const directory = path.join(root, "04_interactive_presentation/data");
  const products = new Map([
    ["evidence-history.json", serialise(history)],
    ["evidence-history.js", "window.REACTOR_EVIDENCE_HISTORY = " + JSON.stringify(history) + ";\n"],
  ]);
  const stage = fs.mkdtempSync(path.join(directory, ".history-build-"));
  const originals = new Map();
  const published = [];
  try {
    for (const [name, content] of products) fs.writeFileSync(path.join(stage, name), content);
    for (const name of products.keys()) {
      const target = path.join(directory, name);
      originals.set(name, fs.existsSync(target) ? fs.readFileSync(target) : null);
      fs.renameSync(path.join(stage, name), target);
      published.push(name);
    }
  } catch (error) {
    for (const name of published.reverse()) {
      const target = path.join(directory, name);
      const original = originals.get(name);
      if (original === null) fs.unlinkSync(target);
      else fs.writeFileSync(target, original);
    }
    throw error;
  } finally {
    fs.rmSync(stage, { recursive: true });
  }
  return { snapshots: history.snapshots.length, observations: history.imports.length };
}

/**
 * Execute an explicit import, source-bound review or deterministic product build.
 * @param {string[]} args Actual CLI arguments; outputs of imports/reviews must not exist.
 * @returns {Promise<object>} Counts or proposal state, without diagnostics or source text.
 * @throws {Error} On malformed modes, unreadable/altered inputs or existing output files.
 */
async function run(args) {
  if (args.length === 5 && args[0] === "--import") {
    const prior = read(args[1]);
    const history = await globalThis.AtlasEvidenceHistory.importProfiles(prior, read(args[2]), args[3]);
    writeNew(args[4], history);
    return { snapshots: history.snapshots.length, observations: history.imports.length };
  }
  if (args.length === 4 && args[0] === "--initialise") {
    const history = await globalThis.AtlasEvidenceHistory.importProfiles(null, read(args[1]), args[2]);
    writeNew(args[3], history);
    return { snapshots: history.snapshots.length, observations: history.imports.length };
  }
  if (args.length === 4 && args[0] === "--review") {
    const reviewed = await globalThis.AtlasEvidenceCorrections.reviewProposal(read(args[1]), read(args[2]));
    writeNew(args[3], reviewed);
    return { state: reviewed.state, publication_effect: reviewed.publication_effect };
  }
  if (args.length === 2 && args[0] === "--build") return build(args[1]);
  throw new Error("Usage: evidence_history.cjs --initialise PROFILES OBSERVED_AT NEW_OUTPUT | --import HISTORY PROFILES OBSERVED_AT NEW_OUTPUT | --review PROPOSAL REVIEW NEW_OUTPUT | --build ROOT");
}

module.exports = { build, run };
if (require.main === module) {
  run(process.argv.slice(2)).then(result => {
    process.stdout.write(JSON.stringify(result) + "\n");
  }).catch(() => {
    process.stderr.write("Evidence history command refused: its inputs, dates, output paths or retained source content are unavailable or invalid.\n");
    process.exitCode = 2;
  });
}
