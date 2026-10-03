// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — historical navigation and locally prepared correction proposals
"use strict";

(() => {
  /**
   * Bind actual journal controls and preserve proposal/source custody boundaries.
   * @returns {Promise<void>} Initialisation and source-bound event handlers.
   */
  async function start() {
    const api = globalThis.AtlasEvidenceHistoryRender;
    const content = structuredClone(window.REACTOR_EVIDENCE_HISTORY);
    const entry = document.getElementById("historyEntry");
    const claim = document.getElementById("historyClaim");
    const revisionSelect = document.getElementById("historyRevision");
    const view = document.getElementById("historyView");
    const status = document.getElementById("historyStatus");
    const share = document.getElementById("historyShare");
    const download = document.getElementById("historyDownload");
    const form = document.getElementById("correctionForm");
    const fields = document.getElementById("correctionFields");
    const proposalDownload = document.getElementById("correctionDownload");
    const proposalStatus = document.getElementById("correctionStatus");
    let currentHash;
    let current;
    let generation = 0;

    function disable(link) {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
    }

    function reset() {
      for (const link of [share, download, proposalDownload]) disable(link);
      fields.disabled = true;
      proposalStatus.textContent = "";
      current = undefined;
    }

    function refuse() {
      reset();
      view.replaceChildren();
      status.textContent = "This historical revision could not be restored. Its linked journal, claim or dated revision is unavailable. Choose an available entry to continue.";
    }

    function populateClaims(entryId) {
      const claims = new Map();
      for (const snapshot of content.snapshots) {
        const profile = snapshot.document.records.find(record => record.entry_id === entryId);
        if (profile) for (const original of profile.claims) claims.set(original.claim_id, original.topic);
      }
      claim.replaceChildren(...Array.from(claims, ([id, topic]) => new Option(topic + " · " + id, id)));
    }

    function enableDownload(link, value, name) {
      link.href = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(value, null, 2) + "\n");
      link.download = name;
      link.removeAttribute("aria-disabled");
    }

    async function show(expected, entryId, claimId, revisionHash, writeHistory) {
      const selectedGeneration = ++generation;
      reset();
      view.replaceChildren();
      status.textContent = "Loading the retained original revision.";
      try {
        const result = await api.render(content, expected, entryId, claimId, revisionHash);
        if (selectedGeneration !== generation) return;
        const url = api.shareUrl(window.location.href, expected, entryId, claimId, result.selected.revision_sha256);
        current = result;
        revisionSelect.replaceChildren(...result.bundle.revisions.map(revision =>
          new Option(revision.dates.atlas_observed_at + " · " + revision.state, revision.revision_sha256)));
        revisionSelect.value = result.selected.revision_sha256;
        view.innerHTML = result.html;
        share.href = url;
        share.removeAttribute("aria-disabled");
        enableDownload(download, result.bundle, entryId + "-claim-history.json");
        fields.disabled = result.selected.state !== "present";
        status.textContent = "History ready. Original source content is retained; proposals require a separate curator decision and source edit.";
        if (writeHistory) window.history.pushState(null, "", url);
      } catch {
        if (selectedGeneration === generation) refuse();
      }
    }

    async function restore() {
      try {
        const state = api.readUrl(window.location.href);
        if (state) {
          entry.value = state.entryId;
          populateClaims(state.entryId);
          claim.value = state.claimId;
        }
        await show(state ? state.historyHash : currentHash, entry.value, claim.value,
          state ? state.revisionHash : null, false);
        if (state) document.getElementById("evidence-history").scrollIntoView();
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
      for (const snapshot of content.snapshots) for (const profile of snapshot.document.records) {
        entries.set(profile.entry_id, profile.taxonomy_record.name);
      }
      entry.replaceChildren(...Array.from(entries, ([id, name]) => new Option(name + " · " + id, id)));
      populateClaims(entry.value);
      await restore();
    } catch {
      refuse();
    }
    entry.addEventListener("change", () => {
      populateClaims(entry.value);
      show(currentHash, entry.value, claim.value, null, true);
    });
    claim.addEventListener("change", () => show(currentHash, entry.value, claim.value, null, true));
    revisionSelect.addEventListener("change", () =>
      show(currentHash, entry.value, claim.value, revisionSelect.value, true));
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const selectedGeneration = generation;
      const selected = current;
      disable(proposalDownload);
      try {
        const input = { ...Object.fromEntries(new FormData(form)), proposed_at: new Date().toISOString() };
        const proposal = await globalThis.AtlasEvidenceCorrections.propose(content, selected.bundle.history_sha256,
          selected.bundle.entry_id, selected.bundle.claim_id, selected.selected.revision_sha256, input);
        if (selectedGeneration !== generation) return;
        enableDownload(proposalDownload, proposal, selected.bundle.entry_id + "-correction-proposal.json");
        proposalStatus.textContent = "Correction proposal prepared locally. Download it for curator review; this page has not submitted it or changed accepted data.";
      } catch {
        if (selectedGeneration === generation) {
          proposalStatus.textContent = "The correction proposal could not be prepared. Check the proposed wording, anonymous HTTPS source, locator and reason.";
        }
      }
    });
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
  }

  globalThis.AtlasEvidenceHistoryController = Object.freeze({ start });
})();
