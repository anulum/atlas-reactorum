// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility-detail-controller.js
"use strict";

/** Actual facility detail selection, original source fields and native dialog. */
var AtlasFacilityDetails = (() => {
  /**
   * Bind original facility identities to the actual shared native dialog.
   * @param {Document} document Actual Atlas document containing the detail body and dialog.
   * @param {import("./application-data.js").ApplicationFacility[]} facilityRows Complete admitted original records in producer order.
   * @returns {{open:(id:string|undefined)=>void}} Original sourced detail view; an absent identity is left unopened.
   */
  function create(document, facilityRows) {
    const elements = globalThis.AtlasBrowserElements;
    const esc = globalThis.AtlasPresentationText.escape;
    const sourceLinks = globalThis.AtlasPresentationText.sourceLinks;

    /**
     * Open original facility details while retaining unknown extra producer cells.
     * @param {string|undefined} id Actual record identity selected by a card or native map.
     * @returns {void} Original sourced details render or an absent record is left unopened.
     */
    function openFacility(id) {
      let x = facilityRows.find((x) => x.id === id);
      if (!x) return;
      let location =
          x.lat !== null &&
          x.lon !== null &&
          Number.isFinite(Number(x.lat)) &&
          Number.isFinite(Number(x.lon))
            ? x.lat + ", " + x.lon
            : "Coordinates unavailable",
        fields = [
          ["Country", x.country],
          ["Plant / parent site", x.plant_name],
          ["Type", x.type],
          ["Sector", x.sector],
          ["Process / activity", x.process_or_activity],
          ["Status", x.status],
          ["Location", location],
          ["Electrical capacity (MW)", x.capacity_mw],
          ["Source nameplate capacity (MW)", x.nameplate_mw],
          ["Net electrical power (MWe)", x.net_mwe],
          ["Gross electrical power (MWe)", x.gross_mwe],
          ["Thermal power (MW)", x.thermal_power_mw || x.thermal_mw],
          ["Industrial capacity", x.capacity],
          ["Published purpose / use", x.purpose],
          ["Published fuel / feed classification", x.fuel_or_feed],
          ["Product / reporting context", x.pollutant_or_product_context],
          ["Operator / organisation", x.operator || x.organization],
          ["Owner", x.owner],
          ["Construction start", x.construction_start],
          ["First criticality", x.first_criticality],
          ["First operation", x.first_operation],
          ["Grid connection", x.grid_connection],
          ["Commercial operation", x.commercial_operation],
          [
            "Last operation / shutdown",
            x.permanent_shutdown || x.shutdown_date || x.last_operation,
          ],
          ["Data coverage", x.completeness],
          ["Dataset", x.dataset || x.dataset_source || x.source_dataset],
          ["Source date", x.source_date || x.source_checked || x.retrieved_at],
          ["Quality flag", x.data_quality_flag],
          ["Coverage caveat", x.data_caveat],
          ["Notes", x.notes || x.verification_notes],
        ];
      elements.requireElement(document, "dialogBody", "div").innerHTML =
        `<div class="dialog-body"><span class="kicker">Facility / ${esc(x.domain)}</span><h2 id="dialogTitle">${esc(x.name)}</h2><dl>${fields
          .filter(([, v]) => v !== undefined && v !== null && v !== "")
          .map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`)
          .join(
            "",
          )}</dl>${globalThis.AtlasFacilityFieldSources.render(x)}${window.FacilitySourceAssertions.render(x.research_field_origins || [])}${window.PrimaryResearchAssertions.render(x.research_primary_assertions || [])}<div class="detail-sources">${sourceLinks(x.source_urls || [x.source_url])}</div></div>`;
      elements.requireElement(document, "reactorDialog", "dialog").showModal();
    }
    return Object.freeze({ open: openFacility });
  }
  return Object.freeze({ create });
})();
globalThis.AtlasFacilityDetails = AtlasFacilityDetails;
