// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual learning navigation and source-linked checks
"use strict";

/** Actual source-bound learning navigation, feedback and local download facade. */
var AtlasLearningPathController = (() => {
  /**
   * Bind the real learning controls to the same source profiles as research views.
   * @param {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} rows Actual complete production taxonomy rows, never display-name identities.
   * @returns {Promise<void>} Initialisation and event bindings with visible source/version refusals.
   */
  async function start(rows) {
    const api = globalThis.AtlasLearningPaths;
    /** @type {import("./browser-contracts.js").AtlasEvidenceDocument} */
    const content = structuredClone(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES);
    const actualRows = structuredClone(rows);
    const controls = globalThis.AtlasBrowserElements;
    const select = controls.requireElement(document, "learningPath", "select");
    const depth = controls.requireElement(document, "learningDepth", "select");
    const view = controls.requireElement(document, "learningView", "section");
    const status = controls.requireElement(document, "learningStatus", "p");
    const share = controls.requireElement(document, "learningShare", "a");
    const download = controls.requireElement(document, "learningDownload", "a");
    const compare = controls.requireElement(document, "learningCompare", "a");
    const workspace = controls.requireElement(document, "learn", "section");
    /** @type {import("./learning-paths.js").AtlasLearningSnapshot|null} */
    let currentSnapshot = null;
    let revision = 0;
    select.replaceChildren(
      ...api.listPaths().map((path) => new Option(path.title, path.id)),
    );

    /**
     * Remove obsolete share, download and comparison links before new selection.
     * @returns {void} Actual links declare their disabled state and have no href.
     */
    function disableLinks() {
      for (const link of [share, download, compare]) {
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      }
    }

    /**
     * Display source/version refusal without substituting current learning content.
     * @returns {void} The actual view and all obsolete link targets are cleared.
     */
    function refuse() {
      view.replaceChildren();
      disableLinks();
      status.textContent =
        "This learning path could not be restored. Its linked data, content or example is unavailable. Choose an available path to continue.";
    }

    /**
     * Render only the newest exact original learning route and bind its source check.
     * @param {import("./learning-paths.js").AtlasLearningSnapshot|null} expected Explicit data/content version or unavailable initial version.
     * @param {string} pathId Actual selected stable route identity.
     * @param {string} readingDepth Actual selected overview/research depth.
     * @param {boolean} writeHistory Whether this user selection adds browser history.
     * @returns {Promise<void>} The newest view renders or visibly refuses.
     */
    async function show(expected, pathId, readingDepth, writeHistory) {
      const selectedRevision = ++revision;
      disableLinks();
      view.replaceChildren();
      status.textContent = "Loading the source-bound learning path.";
      try {
        const result = await api.renderPath(
          content,
          expected,
          pathId,
          readingDepth,
          actualRows,
        );
        if (selectedRevision !== revision) return;
        const url = api.shareUrl(
          window.location.href,
          expected,
          pathId,
          readingDepth,
        );
        view.innerHTML = result.html;
        share.href = url;
        download.href =
          "data:application/json;charset=utf-8," +
          encodeURIComponent(JSON.stringify(result.bundle, null, 2) + "\n");
        download.download = pathId + "-learning-session.json";
        compare.href = globalThis.AtlasTaxonomyComparison.shareUrl(
          window.location.href,
          result.bundle.snapshot.profile_sha256,
          result.bundle.path.entry_ids,
        );
        for (const link of [share, download, compare])
          link.removeAttribute("aria-disabled");
        status.textContent =
          "Learning path ready. Both reading depths retain the same original profiles, claims and sources.";
        const check = controls.requireElement(
          document,
          "learningCheck",
          "form",
        );
        const feedbackView = controls.requireElement(
          document,
          "learningFeedback",
          "p",
        );
        check.addEventListener("submit", async (event) => {
          event.preventDefault();
          const answer = new FormData(check).get("learningAnswer");
          try {
            const feedback = await api.assess(
              content,
              expected,
              pathId,
              answer,
            );
            if (selectedRevision === revision) {
              feedbackView.textContent =
                feedback.message +
                " Original statement: " +
                feedback.supporting_claim.original_statement +
                " Support boundary: " +
                feedback.supporting_claim.citation.scope;
            }
          } catch {
            if (selectedRevision === revision) refuse();
          }
        });
        if (writeHistory) window.history.pushState(null, "", url);
      } catch {
        if (selectedRevision === revision) refuse();
      }
    }

    /**
     * Restore an exact linked source/content version or the current route controls.
     * @returns {Promise<void>} The original linked view renders or visibly refuses.
     */
    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        if (state) {
          select.value = state.pathId;
          depth.value = state.depth;
        }
        await show(
          state ? state.snapshot : currentSnapshot,
          select.value,
          depth.value,
          false,
        );
        if (state) workspace.scrollIntoView();
      } catch {
        ++revision;
        refuse();
      }
    }

    disableLinks();
    try {
      currentSnapshot = await api.snapshot(content);
      await restore();
    } catch {
      refuse();
    }
    for (const control of [select, depth]) {
      control.addEventListener("change", () =>
        show(currentSnapshot, select.value, depth.value, true),
      );
    }
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  return Object.freeze({ start });
})();

globalThis.AtlasLearningPathController = AtlasLearningPathController;
