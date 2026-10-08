// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — complete taxonomy product publication and native rollback.
"use strict";

const fs = require("node:fs");
const path = require("node:path");

/**
 * Prepare the complete export set, then replace its members with rollback.
 * Each rollback record is appended only after its actual rename succeeds.
 * Original bytes and original absence are separate states; no missing product
 * receives invented fallback bytes. Input validation belongs to the exporter
 * and finishes before this transaction is called.
 * @param {string} dataRoot Candidate presentation data directory.
 * @param {Map<string, string>} products Complete named serialized products.
 * @returns {void} Publishes all products, or restores already replaced members.
 * @throws {Error} Native staging, reading, rename, rollback or cleanup fails.
 */
function publishProducts(dataRoot, products) {
  const stage = fs.mkdtempSync(path.join(dataRoot, ".taxonomy-build-"));
  /** @type {{target: string, original: Buffer|null}[]} */
  const published = [];
  try {
    for (const [name, content] of products) {
      fs.writeFileSync(path.join(stage, name), content);
    }
    for (const name of products.keys()) {
      const target = path.join(dataRoot, name);
      const original = fs.existsSync(target) ? fs.readFileSync(target) : null;
      fs.renameSync(path.join(stage, name), target);
      published.push({ target, original });
    }
  } catch (error) {
    for (const { target, original } of published.reverse()) {
      if (original === null) fs.unlinkSync(target);
      else fs.writeFileSync(target, original);
    }
    throw error;
  } finally {
    fs.rmSync(stage, { recursive: true });
  }
}

module.exports = { publishProducts };
