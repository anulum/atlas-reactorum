// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual learning navigation and source-linked checks
"use strict";

(() => {
  /**
   * Bind the real learning controls to the same source profiles as research views.
   * @param {object[]} rows Actual production taxonomy rows, never display-name identities.
   * @returns {Promise<void>} Initialisation and event bindings with visible source/version refusals.
   */
  async function start(rows) {
    const api = globalThis.AtlasLearningPaths;
    const content = structuredClone(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES);
    const actualRows = structuredClone(rows);
    const select = document.getElementById("learningPath");
    const depth = document.getElementById("learningDepth");
    const view = document.getElementById("learningView");
    const status = document.getElementById("learningStatus");
    const share = document.getElementById("learningShare");
    const download = document.getElementById("learningDownload");
    const compare = document.getElementById("learningCompare");
    let currentSnapshot;
    let revision = 0;
    select.replaceChildren(...api.listPaths().map(path => new Option(path.title, path.id)));

    function disableLinks() {
      for (const link of [share, download, compare]) {
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      }
    }

    function refuse() {
      view.replaceChildren();
      disableLinks();
      status.textContent = "This learning path could not be restored. Its linked data, content or example is unavailable. Choose an available path to continue.";
    }

    async function show(expected, pathId, readingDepth, writeHistory) {
      const selectedRevision = ++revision;
      disableLinks();
      view.replaceChildren();
      status.textContent = "Loading the source-bound learning path.";
      try {
        const result = await api.renderPath(content, expected, pathId, readingDepth, actualRows);
        if (selectedRevision !== revision) return;
        const url = api.shareUrl(window.location.href, expected, pathId, readingDepth);
        view.innerHTML = result.html;
        share.href = url;
        download.href = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result.bundle, null, 2) + "\n");
        download.download = pathId + "-learning-session.json";
        compare.href = globalThis.AtlasTaxonomyComparison.shareUrl(
          window.location.href, expected.profile_sha256, result.bundle.path.entry_ids,
        );
        for (const link of [share, download, compare]) link.removeAttribute("aria-disabled");
        status.textContent = "Learning path ready. Both reading depths retain the same original profiles, claims and sources.";
        document.getElementById("learningCheck").addEventListener("submit", async event => {
          event.preventDefault();
          const answer = new FormData(event.currentTarget).get("learningAnswer");
          try {
            const feedback = await api.assess(content, expected, pathId, answer);
            if (selectedRevision === revision) {
              document.getElementById("learningFeedback").textContent =
                feedback.message + " Original statement: " + feedback.supporting_claim.original_statement +
                " Support boundary: " + feedback.supporting_claim.citation.scope;
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

    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        if (state) {
          select.value = state.pathId;
          depth.value = state.depth;
        }
        await show(state ? state.snapshot : currentSnapshot, select.value, depth.value, false);
        if (state) document.getElementById("learn").scrollIntoView();
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
      control.addEventListener("change", () => show(currentSnapshot, select.value, depth.value, true));
    }
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  globalThis.AtlasLearningPathController = Object.freeze({ start });
})();
