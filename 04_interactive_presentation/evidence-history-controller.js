// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — historical navigation and locally prepared correction proposals
"use strict";

/** Actual historical navigation and local correction event facade. */
var AtlasEvidenceHistoryController = (() => {
  /**
   * Bind actual journal controls and preserve proposal/source custody boundaries.
   * @returns {Promise<void>} Initialisation and source-bound event handlers.
   */
  async function start() {
    const api = globalThis.AtlasEvidenceHistoryRender;
    /** @type {import("./browser-contracts.js").AtlasEvidenceJournal} */
    const content = structuredClone(window.REACTOR_EVIDENCE_HISTORY);
    const controls = globalThis.AtlasBrowserElements;
    const entry = controls.requireElement(document, "historyEntry", "select");
    const claim = controls.requireElement(document, "historyClaim", "select");
    const revisionSelect = controls.requireElement(
      document,
      "historyRevision",
      "select",
    );
    const view = controls.requireElement(document, "historyView", "div");
    const status = controls.requireElement(document, "historyStatus", "p");
    const share = controls.requireElement(document, "historyShare", "a");
    const download = controls.requireElement(document, "historyDownload", "a");
    const form = controls.requireElement(document, "correctionForm", "form");
    const fields = controls.requireElement(
      document,
      "correctionFields",
      "fieldset",
    );
    const proposalDownload = controls.requireElement(
      document,
      "correctionDownload",
      "a",
    );
    const proposalStatus = controls.requireElement(
      document,
      "correctionStatus",
      "p",
    );
    const workspace = controls.requireElement(
      document,
      "evidence-history",
      "section",
    );
    let currentHash = "";
    /** @type {Awaited<ReturnType<typeof api.render>>|undefined} */
    let current;
    let generation = 0;

    /**
     * Remove a local share/download target until its current revision is valid.
     * @param {HTMLAnchorElement} link Actual page link.
     * @returns {void} The link has no href and declares its disabled state.
     */
    function disable(link) {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
    }

    /**
     * Invalidate every prior link and proposal before asynchronous selection.
     * @returns {void} The actual controls no longer expose a previous revision.
     */
    function reset() {
      for (const link of [share, download, proposalDownload]) disable(link);
      fields.disabled = true;
      proposalStatus.textContent = "";
      current = undefined;
    }

    /**
     * Present visible historical refusal with source-changing controls disabled.
     * @returns {void} The actual current history view and exports are cleared.
     */
    function refuse() {
      reset();
      view.replaceChildren();
      status.textContent =
        "This historical revision could not be restored. Its linked journal, claim or dated revision is unavailable. Choose an available entry to continue.";
    }

    /**
     * Retain all original stable claims of an entry, including retired claims.
     * @param {string} entryId Actual selected stable entry.
     * @returns {void} Native options preserve original claim identity and topic.
     */
    function populateClaims(entryId) {
      const claims = new Map();
      for (const snapshot of content.snapshots) {
        const profile = snapshot.document.records.find(
          (record) => record.entry_id === entryId,
        );
        if (profile)
          for (const original of profile.claims)
            claims.set(original.claim_id, original.topic);
      }
      claim.replaceChildren(
        ...Array.from(
          claims,
          ([id, topic]) => new Option(topic + " · " + id, id),
        ),
      );
    }

    /**
     * Offer original current content as a local JSON download without submission.
     * @param {HTMLAnchorElement} link Actual download control.
     * @param {import("./evidence-history.js").AtlasClaimHistory|import("./evidence-corrections.js").AtlasCorrectionProposal} value Original current bundle or pending proposal.
     * @param {string} name Stable original entry filename.
     * @returns {void} The actual control holds a complete canonical local download.
     */
    function enableDownload(link, value, name) {
      link.href =
        "data:application/json;charset=utf-8," +
        encodeURIComponent(JSON.stringify(value, null, 2) + "\n");
      link.download = name;
      link.removeAttribute("aria-disabled");
    }

    /**
     * Render only the newest requested original revision and its exact links.
     * @param {string} expected Exact complete journal digest, empty before admission.
     * @param {string} entryId Actual selected stable entry.
     * @param {string} claimId Actual selected stable claim.
     * @param {string|null} revisionHash Explicit dated revision or the last observation.
     * @param {boolean} writeHistory Whether this user selection adds browser history.
     * @returns {Promise<void>} The newest selection renders or visibly refuses.
     */
    async function show(
      expected,
      entryId,
      claimId,
      revisionHash,
      writeHistory,
    ) {
      const selectedGeneration = ++generation;
      reset();
      view.replaceChildren();
      status.textContent = "Loading the retained original revision.";
      try {
        const result = await api.render(
          content,
          expected,
          entryId,
          claimId,
          revisionHash,
        );
        if (selectedGeneration !== generation) return;
        const url = api.shareUrl(
          window.location.href,
          expected,
          entryId,
          claimId,
          result.selected.revision_sha256,
        );
        current = result;
        revisionSelect.replaceChildren(
          ...result.bundle.revisions.map(
            (revision) =>
              new Option(
                revision.dates.atlas_observed_at + " · " + revision.state,
                revision.revision_sha256,
              ),
          ),
        );
        revisionSelect.value = result.selected.revision_sha256;
        view.innerHTML = result.html;
        share.href = url;
        share.removeAttribute("aria-disabled");
        enableDownload(
          download,
          result.bundle,
          entryId + "-claim-history.json",
        );
        fields.disabled = result.selected.state !== "present";
        status.textContent =
          "History ready. Original source content is retained; proposals require a separate curator decision and source edit.";
        if (writeHistory) window.history.pushState(null, "", url);
      } catch {
        if (selectedGeneration === generation) refuse();
      }
    }

    /**
     * Restore exact URL identities or the current stable default without an alias.
     * @returns {Promise<void>} The actual linked revision renders or visibly refuses.
     */
    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        if (state) {
          entry.value = state.entryId;
          populateClaims(state.entryId);
          claim.value = state.claimId;
        }
        await show(
          state ? state.historyHash : currentHash,
          entry.value,
          claim.value,
          state ? state.revisionHash : null,
          false,
        );
        if (state) workspace.scrollIntoView();
      } catch {
        ++generation;
        refuse();
      }
    }

    reset();
    try {
      await globalThis.AtlasEvidenceHistory.validate(content);
      currentHash = await globalThis.AtlasEvidenceHistory.digest(content);
      const entries = new Map();
      for (const snapshot of content.snapshots)
        for (const profile of snapshot.document.records) {
          entries.set(profile.entry_id, profile.taxonomy_record.name);
        }
      entry.replaceChildren(
        ...Array.from(
          entries,
          ([id, name]) => new Option(name + " · " + id, id),
        ),
      );
      populateClaims(entry.value);
      await restore();
    } catch {
      refuse();
    }
    entry.addEventListener("change", () => {
      populateClaims(entry.value);
      show(currentHash, entry.value, claim.value, null, true);
    });
    claim.addEventListener("change", () =>
      show(currentHash, entry.value, claim.value, null, true),
    );
    revisionSelect.addEventListener("change", () =>
      show(currentHash, entry.value, claim.value, revisionSelect.value, true),
    );
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const selectedGeneration = generation;
      const selected = current;
      disable(proposalDownload);
      try {
        if (!selected)
          throw new Error("Original correction revision is unavailable");
        const input = {
          ...Object.fromEntries(new FormData(form)),
          proposed_at: new Date().toISOString(),
        };
        const proposal = await globalThis.AtlasEvidenceCorrections.propose(
          content,
          selected.bundle.history_sha256,
          selected.bundle.entry_id,
          selected.bundle.claim_id,
          selected.selected.revision_sha256,
          input,
        );
        if (selectedGeneration !== generation) return;
        enableDownload(
          proposalDownload,
          proposal,
          selected.bundle.entry_id + "-correction-proposal.json",
        );
        proposalStatus.textContent =
          "Correction proposal prepared locally. Download it for curator review; this page has not submitted it or changed accepted data.";
      } catch {
        if (selectedGeneration === generation) {
          proposalStatus.textContent =
            "The correction proposal could not be prepared. Check the proposed wording, anonymous HTTPS source, locator and reason.";
        }
      }
    });
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  return Object.freeze({ start });
})();

globalThis.AtlasEvidenceHistoryController = AtlasEvidenceHistoryController;
