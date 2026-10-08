// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — repository-catalogue-controller.js
"use strict";

/** Retained repository metadata cards and search controls. */
var AtlasRepositoryCatalogue = (() => {
  /**
   * Bind repository search to the retained source metadata and safe card links.
   * @param {Document} document Actual repository section and text control.
   * @param {import("./application-data.js").ApplicationRepository[]} repositoryRows Admitted original catalogue metadata.
   * @returns {{start:()=>void,render:()=>void}} Search initialization and original filtered cards.
   */
  function create(document, repositoryRows) {
    const elements = globalThis.AtlasBrowserElements;
    const esc = globalThis.AtlasPresentationText.escape;
    const safeUrl = globalThis.AtlasPresentationText.safeUrl;

    /**
     * Filter the retained repository snapshot by its original descriptive metadata.
     * @returns {void} Matching source cards render without technical capability admission.
     */
    function renderRepos() {
      let q = elements
          .requireElement(document, "repoSearch", "input")
          .value.toLowerCase(),
        repos = repositoryRows;
      elements.requireElement(document, "repoGrid", "div").innerHTML =
        repos
          .filter((r) =>
            [r.name, r.description, r.category, r.topics]
              .flat()
              .join(" ")
              .toLowerCase()
              .includes(q),
          )
          .map(
            (r) =>
              `<a class="repo-card" href="${safeUrl(r.url)}" target="_blank" rel="noopener"><span>${esc(r.category)}</span><h4>${esc(r.name)}</h4><p>${esc(r.description)}</p><small>Updated ${esc(r.updated_at.slice(0, 10))} · ${esc(r.license)}</small></a>`,
          )
          .join("") || "<p>No matching reactor-system repositories.</p>";
    }
    /**
     * Render the retained catalogue and bind its actual text-search control.
     * @returns {void} Original source cards and their input handler are ready.
     */
    function start() {
      renderRepos();
      elements.requireElement(document, "repoSearch", "input").oninput =
        renderRepos;
    }
    return Object.freeze({ start, render: renderRepos });
  }
  return Object.freeze({ create });
})();
globalThis.AtlasRepositoryCatalogue = AtlasRepositoryCatalogue;
