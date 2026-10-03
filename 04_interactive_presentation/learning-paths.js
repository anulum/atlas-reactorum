// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — learning paths bound to original profiles and claims
"use strict";

(() => {
  const catalogue = structuredClone(globalThis.AtlasLearningCatalogue);
  const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  const escape = value => String(value).replace(/[&<>"']/g, character => entities[character]);
  const hashPattern = /^[a-f0-9]{64}$/;
  const depths = ["overview", "research"];

  async function digest(value) {
    const bytes = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(value)));
    return Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function selection(pathId, depth) {
    const path = catalogue.paths.find(path => path.id === pathId);
    if (!path || !depths.includes(depth)) throw new Error("Learning path or reading depth is unavailable");
    return path;
  }

  function checkHashes(expected) {
    if (!expected || !hashPattern.test(expected.profile_sha256) || !hashPattern.test(expected.learning_sha256)) {
      throw new Error("Learning snapshot hashes are invalid");
    }
  }

  /**
   * Return the authored questions without changing their source identities.
   * @returns {object[]} Independent path metadata, including the explicit learning checks.
   */
  function listPaths() {
    return structuredClone(catalogue.paths);
  }

  /**
   * Identify the full profile data and all authored learning content separately.
   * @param {object} document Complete source-bound profile document.
   * @returns {Promise<object>} Explicit SHA-256 digests of data and learning definitions.
   * @throws {Error} When the complete profile document is unavailable or unsupported.
   */
  async function snapshot(document) {
    return { profile_sha256: await globalThis.AtlasTaxonomyComparison.snapshot(document),
      learning_sha256: await digest(catalogue) };
  }

  /**
   * Read a whole learning path against its explicit data/content version.
   * @param {object} document Complete source-bound profile document.
   * @param {object} expected Explicit profile_sha256 and learning_sha256 digests.
   * @param {string} pathId Stable authored question-path identity.
   * @returns {Promise<object>} Original profiles, claims, sources, rights and the bound question.
   * @throws {Error} On stale versions, missing examples or changed supporting statements.
   */
  async function readPath(document, expected, pathId) {
    checkHashes(expected);
    const content = structuredClone(document);
    const path = selection(pathId, "overview");
    const actual = await snapshot(content);
    if (actual.profile_sha256 !== expected.profile_sha256 || actual.learning_sha256 !== expected.learning_sha256) {
      throw new Error("The linked learning snapshot is unavailable; current content was not substituted");
    }
    const entries = path.entry_ids.map(id => JSON.parse(globalThis.AtlasTaxonomyEvidenceProfiles.exportProfile(
      content, content.inputs.taxonomy_sha256, id,
    )));
    const answer = entries.find(entry => entry.profile.entry_id === path.answer_entry_id).profile;
    const claim = answer.claims.find(claim => claim.claim_id === path.answer_claim_id);
    if (!claim || claim.original_statement !== path.answer_statement ||
        claim.citation.id !== path.answer_claim_id || claim.citation.statement !== path.answer_statement) {
      throw new Error("The learning check's original source statement is unavailable or changed");
    }
    const used = new Set(entries.flatMap(entry => entry.sources.map(source => source.id)));
    return { schema_version: "atlas-learning-session-1.0.0", metadata_license: "AGPL-3.0-or-later",
      source_rights: "catalogue-only; original not redistributed", inputs: content.inputs, snapshot: actual,
      path: structuredClone(path), profiles: entries.map(entry => entry.profile),
      sources: content.sources.filter(source => used.has(source.id)) };
  }

  /**
   * Check an answer against the same original claim shown in both reading depths.
   * @param {object} document Complete source-bound profile document.
   * @param {object} expected Explicit data/content snapshot digests.
   * @param {string} pathId Stable learning-path identity.
   * @param {string} answerId One example identity or the explicit not-established choice.
   * @returns {Promise<object>} Source-linked feedback; no human-comprehension or scientific score.
   * @throws {Error} On an unavailable path/snapshot or a choice outside its examples.
   */
  async function assess(document, expected, pathId, answerId) {
    const bundle = await readPath(document, expected, pathId);
    if (![...bundle.path.entry_ids, "not-established"].includes(answerId)) {
      throw new Error("Learning answer is outside this path");
    }
    const correct = answerId === bundle.path.answer_entry_id;
    const profile = bundle.profiles.find(profile => profile.entry_id === bundle.path.answer_entry_id);
    const claim = profile.claims.find(claim => claim.claim_id === bundle.path.answer_claim_id);
    return { correct, message: correct ? "Your choice matches the cited statement." :
      "Re-read the cited statement and its scope, then try again.",
      supporting_claim: structuredClone(claim), snapshot: bundle.snapshot };
  }

  /**
   * Render original example statements, evidence and an accessible learning check.
   * @param {object} document Complete source-bound profile document.
   * @param {object} expected Explicit data/content snapshot digests.
   * @param {string} pathId Stable learning-path identity.
   * @param {string} depth overview or research; the original evidence bundle is identical.
   * @param {object[]} rows Actual production taxonomy rows, used to verify profile parity.
   * @returns {Promise<object>} Escaped presentation and its identical downloadable evidence bundle.
   * @throws {Error} On unsupported depth or a missing/altered actual taxonomy example.
   */
  async function renderPath(document, expected, pathId, depth, rows) {
    const content = structuredClone(document);
    const actualRows = structuredClone(rows);
    selection(pathId, depth);
    const bundle = await readPath(content, expected, pathId);
    const examples = bundle.profiles.map(profile => {
      const row = actualRows.find(row => row.id === profile.entry_id);
      if (!row) throw new Error("The actual learning example is unavailable");
      const full = globalThis.AtlasTaxonomyEvidenceProfiles.render(content, content.inputs.taxonomy_sha256, row);
      const evidence = depth === "research" ? full :
        "<details><summary>Inspect the original evidence profile and sources</summary>" + full + "</details>";
      return "<article class='learning-example'><h4>" + escape(row.name) + "</h4><p class='learning-principle'>" +
        escape(profile.taxonomy_record.principle) + "</p><p><strong>Original challenge:</strong> " +
        escape(profile.taxonomy_record.challenge) + "</p><p><strong>Original evidence scope:</strong> " +
        escape(profile.taxonomy_record.evidence_scope) + "</p>" + evidence + "</article>";
    }).join("");
    const choices = bundle.profiles.map(profile => "<label><input type='radio' name='learningAnswer' value='" +
      escape(profile.entry_id) + "' required> " + escape(profile.taxonomy_record.name) + "</label>").join("");
    const glossary = catalogue.glossary.map(entry => "<div><dt>" + escape(entry.term) +
      "</dt><dd>" + escape(entry.meaning) + "</dd></div>").join("");
    const html = "<h3 id='learningPathTitle'>" + escape(bundle.path.title) + "</h3><p><strong>Learning goal:</strong> " +
      escape(bundle.path.objective) + "</p><p>" + escape(bundle.path.prompt) + "</p>" +
      "<ol class='learning-steps' aria-label='Reading route'><li>Read the original principle</li><li>Inspect its source locator</li>" +
      "<li>Check the stated limit</li><li>Compare the same profiles</li></ol><div class='learning-examples'>" + examples + "</div>" +
      "<p class='learning-limit'><strong>Keep this limit:</strong> " + escape(bundle.path.limitation) + "</p>" +
      "<form id='learningCheck'><fieldset><legend>" + escape(bundle.path.question) + "</legend>" + choices +
      "<label><input type='radio' name='learningAnswer' value='not-established' required> Not established by these statements</label>" +
      "</fieldset><button type='submit' class='primary'>Check against the source</button></form>" +
      "<p id='learningFeedback' role='status' aria-live='polite'></p>" +
      "<details class='learning-glossary'><summary>Terms used in this path</summary><dl>" + glossary + "</dl></details>";
    return { bundle, html };
  }

  /**
   * Share a selected learning path with its content, data and reading-depth version.
   * @param {string} pageUrl Anonymous absolute http, https or file presentation URL.
   * @param {object} expected Explicit data/content snapshot digests.
   * @param {string} pathId Stable question-path identity.
   * @param {string} depth overview or research.
   * @returns {string} Versioned fragment link preserving the original static page/query.
   * @throws {Error} On invalid digests, unavailable selections or unsupported page URLs.
   */
  function shareUrl(pageUrl, expected, pathId, depth) {
    checkHashes(expected);
    selection(pathId, depth);
    const url = new URL(pageUrl);
    if (!["https:", "http:", "file:"].includes(url.protocol) || url.username || url.password) {
      throw new Error("Learning page URL is unsupported");
    }
    url.hash = "learn?" + new URLSearchParams({ version: "1", profile: expected.profile_sha256,
      lesson: expected.learning_sha256, path: pathId, view: depth }).toString();
    return url.href;
  }

  /**
   * Parse only exact learning links; ordinary anchors remain ordinary navigation.
   * @param {string} pageUrl Absolute current presentation URL.
   * @returns {object|null} Explicit snapshot/path/depth, or null for another page anchor.
   * @throws {Error} On unknown, duplicated, missing or unavailable linked fields.
   */
  function readUrl(pageUrl) {
    const hash = new URL(pageUrl).hash;
    if (!hash.startsWith("#learn?")) return null;
    const query = new URLSearchParams(hash.slice(7));
    const fields = ["version", "profile", "lesson", "path", "view"];
    if (fields.some(field => query.getAll(field).length !== 1) || query.get("version") !== "1" ||
        [...query.keys()].some(field => !fields.includes(field))) {
      throw new Error("Shared learning format is unavailable or invalid");
    }
    const expected = { profile_sha256: query.get("profile"), learning_sha256: query.get("lesson") };
    checkHashes(expected);
    selection(query.get("path"), query.get("view"));
    return { snapshot: expected, pathId: query.get("path"), depth: query.get("view") };
  }

  globalThis.AtlasLearningPaths = Object.freeze({ listPaths, snapshot, readPath, assess, renderPath, shareUrl, readUrl });
})();
