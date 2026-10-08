// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — comparison controls and actual browser navigation
"use strict";

/** Actual source-bound comparison navigation and local download facade. */
var AtlasTaxonomyComparisonController = (() => {
  /**
   * Wire stable-ID choices, browser history, refusal status and JSON downloads.
   * @param {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} rows Actual complete source-bound taxonomy rows loaded by the presentation.
   * @returns {Promise<void>} Resolves after the initial comparison or visible refusal.
   */
  async function start(rows) {
    const api = globalThis.AtlasTaxonomyComparison;
    /** @type {import("./browser-contracts.js").AtlasEvidenceDocument} */
    const document = structuredClone(window.REACTOR_TAXONOMY_EVIDENCE_PROFILES);
    const controls = globalThis.AtlasBrowserElements;
    const selects = ["compareA", "compareB", "compareC"].map((id) =>
      controls.requireElement(window.document, id, "select"),
    );
    const view = controls.requireElement(window.document, "compareView", "div");
    const status = controls.requireElement(
      window.document,
      "compareStatus",
      "p",
    );
    const share = controls.requireElement(window.document, "compareShare", "a");
    const download = controls.requireElement(
      window.document,
      "compareDownload",
      "a",
    );
    const workspace = controls.requireElement(
      window.document,
      "compare",
      "section",
    );
    let revision = 0;
    let currentSnapshot = "";
    /**
     * Remove stale share/download links before every asynchronous selection.
     * @returns {void} Actual links have no target and declare their disabled state.
     */
    const disableExports = () => {
      share.removeAttribute("href");
      download.removeAttribute("href");
      share.setAttribute("aria-disabled", "true");
      download.setAttribute("aria-disabled", "true");
    };
    /**
     * Present exact-version refusal without substituting current profiles.
     * @returns {void} The actual view and exports no longer expose a prior result.
     */
    const refusal = () => {
      view.replaceChildren();
      disableExports();
      status.textContent =
        "This comparison could not be restored. Check that the linked data version is available and choose two or three different entries. Current data have not replaced the linked snapshot.";
    };
    for (const [i, select] of selects.entries()) {
      select.replaceChildren();
      if (i === 2) select.add(new Option("— optional —", ""));
      for (const row of rows) select.add(new Option(row.name, row.id));
    }
    const defaults = ["fission", "fusion"].map((domain) => {
      const row = rows.find((row) => row.domain === domain);
      if (!row)
        throw new Error("Original comparison domain is unavailable: " + domain);
      return row.id;
    });
    selects[0].value = defaults[0];
    selects[1].value = defaults[1];

    /**
     * Render only the newest requested original profile selection and its links.
     * @param {string} expected Complete expected profile digest, empty before admission.
     * @param {string[]} ids Two or three stable entry identities in display order.
     * @param {boolean} writeHistory Whether this user selection adds browser history.
     * @returns {Promise<void>} The newest comparison renders or visibly refuses.
     */
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
        download.href =
          "data:application/json;charset=utf-8," +
          encodeURIComponent(JSON.stringify(result.bundle, null, 2) + "\n");
        download.removeAttribute("aria-disabled");
        download.download = "atlas-reactorum-comparison.json";
        status.textContent =
          "Comparison ready. The link and download retain this data version, selection and source citations.";
        if (writeHistory) window.history.pushState(null, "", url);
      } catch {
        if (selectedRevision === revision) refusal();
      }
    }

    /**
     * Restore an exact versioned link or the original default stable identities.
     * @returns {Promise<void>} Linked source content renders or visibly refuses.
     */
    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        const ids = state ? state.entryIds : defaults;
        for (const [i, select] of selects.entries())
          select.value = ids[i] || "";
        await show(state ? state.snapshot : currentSnapshot, ids, false);
        if (state) workspace.scrollIntoView();
      } catch {
        ++revision;
        refusal();
      }
    }

    disableExports();
    try {
      currentSnapshot = await api.snapshot(document);
      if (api.readUrl(window.location.href)) await restore();
      else
        await show(
          currentSnapshot,
          selects.slice(0, 2).map((select) => select.value),
          false,
        );
    } catch {
      refusal();
    }
    selects.forEach((select) =>
      select.addEventListener("change", () => {
        show(
          currentSnapshot,
          selects.map((select) => select.value).filter(Boolean),
          true,
        );
      }),
    );
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  return Object.freeze({ start });
})();

globalThis.AtlasTaxonomyComparisonController =
  AtlasTaxonomyComparisonController;
