// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — comparison controls and actual browser navigation
"use strict";

(() => {
  /**
   * Wire stable-ID choices, browser history, refusal status and JSON downloads.
   * @param {object[]} rows Actual complete taxonomy rows loaded by the presentation.
   * @returns {Promise<void>} Resolves after the initial comparison or visible refusal.
   */
  async function start(rows) {
    const api = globalThis.AtlasTaxonomyComparison;
    const document = structuredClone(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES);
    const selects = ["compareA", "compareB", "compareC"].map(id => window.document.getElementById(id));
    const view = window.document.getElementById("compareView");
    const status = window.document.getElementById("compareStatus");
    const share = window.document.getElementById("compareShare");
    const download = window.document.getElementById("compareDownload");
    let revision = 0;
    let currentSnapshot;
    const disableExports = () => {
      share.removeAttribute("href");
      download.removeAttribute("href");
      share.setAttribute("aria-disabled", "true");
      download.setAttribute("aria-disabled", "true");
    };
    const refusal = () => {
      view.replaceChildren();
      disableExports();
      status.textContent = "This comparison could not be restored. Check that the linked data version is available and choose two or three different entries. Current data have not replaced the linked snapshot.";
    };
    for (const [i, select] of selects.entries()) {
      select.replaceChildren();
      if (i === 2) select.add(new Option("— optional —", ""));
      for (const row of rows) select.add(new Option(row.name, row.id));
    }
    const defaults = ["fission", "fusion"].map(domain => rows.find(row => row.domain === domain).id);
    selects[0].value = defaults[0];
    selects[1].value = defaults[1];

    async function show(expected, ids, writeHistory) {
      const selectedRevision = ++revision;
      disableExports();
      status.textContent = "Preparing the source-linked comparison…";
      try {
        const result = await api.renderComparison(document, expected, ids);
        if (selectedRevision !== revision) return;
        const url = api.shareUrl(window.location.href, expected, ids);
        view.innerHTML = result.html;
        share.href = url;
        share.removeAttribute("aria-disabled");
        download.href = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result.bundle, null, 2) + "\n");
        download.removeAttribute("aria-disabled");
        download.download = "atlas-reactorum-comparison.json";
        status.textContent = "Comparison ready. The link and download retain this data version, selection and source citations.";
        if (writeHistory) window.history.pushState(null, "", url);
      } catch {
        if (selectedRevision === revision) refusal();
      }
    }

    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        const ids = state ? state.entryIds : defaults;
        for (const [i, select] of selects.entries()) select.value = ids[i] || "";
        await show(state ? state.snapshot : currentSnapshot, ids, false);
        if (state) window.document.getElementById("compare").scrollIntoView();
      } catch {
        ++revision;
        refusal();
      }
    }

    disableExports();
    try {
      currentSnapshot = await api.snapshot(document);
      if (api.readUrl(window.location.href)) await restore();
      else await show(currentSnapshot, selects.slice(0, 2).map(select => select.value), false);
    } catch {
      refusal();
    }
    selects.forEach(select => select.addEventListener("change", () => {
      show(currentSnapshot, selects.map(select => select.value).filter(Boolean), true);
    }));
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  globalThis.AtlasTaxonomyComparisonController = Object.freeze({ start });
})();
