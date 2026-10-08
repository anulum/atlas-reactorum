// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — 04_interactive_presentation/app.js
"use strict";
const facilityRows = globalThis.AtlasApplicationData.facilities(
  window.REACTOR_FACILITIES,
);
const companyRows = globalThis.AtlasApplicationData.companies(
  window.FUSION_COMPANIES,
);
const taxonomyRows = globalThis.AtlasApplicationData.taxonomy(
  window.REACTOR_TAXONOMY,
);
const taxonomyAuditRows = globalThis.AtlasApplicationData.audits(
  window.REACTOR_TAXONOMY_AUDIT,
);
const repositoryRows = globalThis.AtlasApplicationData.repositories(
  window.ANULUM_REACTOR_REPOS,
);
window.REACTOR_FACILITIES = facilityRows;
window.FUSION_COMPANIES = companyRows;
window.REACTOR_TAXONOMY = taxonomyRows;
window.REACTOR_TAXONOMY_AUDIT = taxonomyAuditRows;
window.ANULUM_REACTOR_REPOS = repositoryRows;

const taxonomyCatalogue = globalThis.AtlasTaxonomyCatalogue.create(
  document,
  taxonomyRows,
  taxonomyAuditRows,
);
const companyCatalogue = globalThis.AtlasCompanyCatalogue.create(
  document,
  companyRows,
);
const repositoryCatalogue = globalThis.AtlasRepositoryCatalogue.create(
  document,
  repositoryRows,
);
const facilityCatalogue = globalThis.AtlasFacilityCatalogue.create(
  document,
  facilityRows,
);
const reactors = taxonomyCatalogue.rows;
globalThis.openReactor = taxonomyCatalogue.open;
globalThis.openFacility = facilityCatalogue.open;
globalThis.filteredFacilities = facilityCatalogue.filtered;
globalThis.downloadFacilityData = facilityCatalogue.download;
const elements = globalThis.AtlasBrowserElements;
/** @type {import("./browser-contracts.js").AtlasFacilityMap|null} */
globalThis.atlasMap = null;

/**
 * Render the selected original fusion explanation in the actual page.
 * @param {string|undefined} kind Actual authored control identity.
 * @returns {void} Original authored content is displayed.
 */
function renderFusion(kind) {
  globalThis.AtlasExplanatoryPanels.renderFusion(document, kind);
}
/**
 * Render the selected original flow explanation in the actual page.
 * @param {string|undefined} kind Actual authored control identity.
 * @returns {void} Original authored content is displayed.
 */
function renderFlow(kind) {
  globalThis.AtlasExplanatoryPanels.renderFlow(document, kind);
}
/**
 * Bind original actual page navigation and dialog controls through their DOM owner.
 * @returns {void} Navigation and dismissal are ready on the maintained page.
 */
function initNav() {
  globalThis.pageNavigation = globalThis.AtlasPageNavigation.start(document);
}
document.addEventListener("DOMContentLoaded", () => {
  elements.requireElement(document, "typeCount", "strong").textContent = String(
    reactors.length,
  );
  taxonomyCatalogue.start();
  globalThis.AtlasTaxonomyComparisonController.start(taxonomyRows);
  globalThis.AtlasLearningPathController.start(taxonomyRows);
  globalThis.AtlasEvidenceHistoryController.start();
  renderFusion("magnetic");
  renderFlow("batch");
  repositoryCatalogue.start();
  facilityCatalogue.start();
  globalThis.atlasMap = facilityCatalogue.map;
  companyCatalogue.start();
  initNav();
  elements.requireElements(document, ".family-tab", "button").forEach(
    (b) =>
      (b.onclick =
        /** Select the authored fusion explanation and retain its active tab state. */ () => {
          elements
            .requireElements(document, ".family-tab", "button")
            .forEach((x) => x.classList.remove("active"));
          b.classList.add("active");
          renderFusion(b.dataset.fusion);
        }),
  );
  elements.requireElements(document, ".flow-selector button", "button").forEach(
    (b) =>
      (b.onclick =
        /** Select the authored flow explanation and update its ARIA selection. */ () => {
          elements
            .requireElements(document, ".flow-selector button", "button")
            .forEach((x) => x.setAttribute("aria-selected", "false"));
          b.setAttribute("aria-selected", "true");
          renderFlow(b.dataset.flow);
        }),
  );
});
