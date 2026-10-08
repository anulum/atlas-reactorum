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
const { read } = require("./canonical_json.cjs");
require("../taxonomy-claim-sources.js");
require("../taxonomy-evidence-profile.js");
require("../taxonomy-comparison.js");
require("../evidence-history.js");
require("../evidence-corrections.js");

/**
 * Retain the original journal's deterministic member order and two-space JSON.
 * @param {unknown} value Original metadata or source-preserving result.
 * @returns {string} Original canonical JSON representation with a final newline.
 */
const serialise = (value) => JSON.stringify(value, null, 2) + "\n";

/**
 * Create a new explicit journal/review file without replacing any prior content.
 * @param {string} file New owner-selected output path.
 * @param {unknown} value Original source-preserving native result.
 * @returns {void} The complete canonical representation was written exclusively.
 * @throws {Error} The path exists or native I/O fails.
 */
function writeNew(file, value) {
  fs.writeFileSync(file, serialise(value), { flag: "wx" });
}

/**
 * Rebuild the two presentation history products from a retained input journal.
 * @param {string} repositoryRoot Complete candidate including current accepted profiles.
 * @returns {Promise<{snapshots: number, observations: number}>} Validated snapshot and observation counts; no acquisition occurs.
 * @throws {Error} If the accepted profiles differ or input/output custody is unavailable.
 */
async function build(repositoryRoot) {
  const root = path.resolve(repositoryRoot);
  const history =
    /** @type {import("../evidence-history.js").AtlasEvidenceJournal} */ (
      read(path.join(root, "metadata/evidence_history/history.json"), "history")
    );
  await globalThis.AtlasEvidenceHistory.validate(history);
  const profiles =
    /** @type {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
      read(
        path.join(
          root,
          "04_interactive_presentation/data/taxonomy-evidence-profiles.json",
        ),
        "profiles",
      )
    );
  if (
    (await globalThis.AtlasTaxonomyComparison.snapshot(profiles)) !==
    history.imports[history.imports.length - 1].profile_sha256
  ) {
    throw new Error(
      "Current profiles differ from the last explicitly imported history snapshot",
    );
  }
  const directory = path.join(root, "04_interactive_presentation/data");
  const products = new Map([
    ["evidence-history.json", serialise(history)],
    [
      "evidence-history.js",
      "window.REACTOR_EVIDENCE_HISTORY = " + JSON.stringify(history) + ";\n",
    ],
  ]);
  const stage = fs.mkdtempSync(path.join(directory, ".history-build-"));
  /** @type {Map<string, Buffer|null>} */
  const originals = new Map();
  /** @type {string[]} */
  const published = [];
  try {
    for (const [name, content] of products)
      fs.writeFileSync(path.join(stage, name), content);
    for (const name of products.keys()) {
      const target = path.join(directory, name);
      originals.set(
        name,
        fs.existsSync(target) ? fs.readFileSync(target) : null,
      );
      fs.renameSync(path.join(stage, name), target);
      published.push(name);
    }
  } catch (error) {
    for (const name of published.reverse()) {
      const target = path.join(directory, name);
      const original = /** @type {Buffer|null} */ (originals.get(name));
      if (original === null) fs.unlinkSync(target);
      else fs.writeFileSync(target, original);
    }
    throw error;
  } finally {
    fs.rmSync(stage, { recursive: true });
  }
  return {
    snapshots: history.snapshots.length,
    observations: history.imports.length,
  };
}

/**
 * Execute an explicit import, source-bound review or deterministic product build.
 * @param {string[]} args Actual CLI arguments; outputs of imports/reviews must not exist.
 * @returns {Promise<{snapshots: number, observations: number}|{state: string, publication_effect: string}>} Counts or proposal state, without diagnostics or source text.
 * @throws {Error} On malformed modes, unreadable/altered inputs or existing output files.
 */
async function run(args) {
  if (args.length === 5 && args[0] === "--import") {
    const prior =
      /** @type {import("../evidence-history.js").AtlasEvidenceJournal} */ (
        read(args[1], "history")
      );
    const profiles =
      /** @type {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
        read(args[2], "profiles")
      );
    const history = await globalThis.AtlasEvidenceHistory.importProfiles(
      prior,
      profiles,
      args[3],
    );
    writeNew(args[4], history);
    return {
      snapshots: history.snapshots.length,
      observations: history.imports.length,
    };
  }
  if (args.length === 4 && args[0] === "--initialise") {
    const profiles =
      /** @type {import("../taxonomy-evidence-profile.js").AtlasEvidenceDocument} */ (
        read(args[1], "profiles")
      );
    const history = await globalThis.AtlasEvidenceHistory.importProfiles(
      null,
      profiles,
      args[2],
    );
    writeNew(args[3], history);
    return {
      snapshots: history.snapshots.length,
      observations: history.imports.length,
    };
  }
  if (args.length === 4 && args[0] === "--review") {
    const proposal =
      /** @type {import("../evidence-corrections.js").AtlasCorrectionProposal} */ (
        read(args[1], "proposal")
      );
    const reviewed = await globalThis.AtlasEvidenceCorrections.reviewProposal(
      proposal,
      read(args[2]),
    );
    writeNew(args[3], reviewed);
    return {
      state: reviewed.state,
      publication_effect: reviewed.publication_effect,
    };
  }
  if (args.length === 2 && args[0] === "--build") return build(args[1]);
  throw new Error(
    "Usage: evidence_history.cjs --initialise PROFILES OBSERVED_AT NEW_OUTPUT | --import HISTORY PROFILES OBSERVED_AT NEW_OUTPUT | --review PROPOSAL REVIEW NEW_OUTPUT | --build ROOT",
  );
}

module.exports = { build, run };
if (require.main === module) {
  run(process.argv.slice(2))
    .then((result) => {
      process.stdout.write(JSON.stringify(result) + "\n");
    })
    .catch(() => {
      process.stderr.write(
        "Evidence history command refused: its inputs, dates, output paths or retained source content are unavailable or invalid.\n",
      );
      process.exitCode = 2;
    });
}
