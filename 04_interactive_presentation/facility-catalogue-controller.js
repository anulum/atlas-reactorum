// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility-catalogue-controller.js
"use strict";

/** Actual facility map/list filters and original complete-data downloads. */
var AtlasFacilityCatalogue = (() => {
  /**
   * Create source filters, native map ownership and complete-data downloads.
   * @param {Document} document Actual Atlas facility section and controls.
   * @param {import("./application-data.js").ApplicationFacility[]} facilityRows Admitted complete original records; filtering never changes their cells.
   * @returns {{start:()=>void,filtered:()=>import("./application-data.js").ApplicationFacility[],download:(format:string)=>void,open:(id:string|undefined)=>void,readonly map:import("./browser-contracts.js").AtlasFacilityMap|null}} Original interactive map/list/export owner and its actual mounted instance.
   */
  function create(document, facilityRows) {
    const elements = globalThis.AtlasBrowserElements;
    const esc = globalThis.AtlasPresentationText.escape;
    const safeUrl = globalThis.AtlasPresentationText.safeUrl;
    const openFacility = globalThis.AtlasFacilityDetails.create(
      document,
      facilityRows,
    ).open;
    /** @type {import("./browser-contracts.js").AtlasFacilityMap|null} */
    let atlasMap = null;
    /**
     * Display the original authored dataset label or unchanged unlabelled source path.
     * @param {string} path Nonempty source-table path selected from the actual source facet.
     * @returns {string} Original dataset context without provenance inference.
     */
    function facilityDatasetLabel(path) {
      /** @type {Record<string, string>} */
      const labels = {
        "05_global_reactor_map/data/reactors.tsv": "WRI historical plant layer",
        "04_interactive_presentation/data/facilities-supplemental.json":
          "Supplemental context records",
        "05_global_reactor_map/imports/fusion/ffdb/fusion_facilities.tsv":
          "IAEA FFDB catalogue (2 October 2026)",
        "05_global_reactor_map/imports/fusion/fusion_facilities.tsv":
          "Fusion device base layer",
        "05_global_reactor_map/imports/fusion/enrichment/new_facilities.tsv":
          "Fusion official-source additions",
        "05_global_reactor_map/imports/research_reactors/research_reactors.tsv":
          "Research reactors",
        "05_global_reactor_map/imports/power_units/power_reactor_units.tsv":
          "GEM power-reactor units",
        "05_global_reactor_map/imports/industrial_facilities/industrial_facilities.tsv":
          "EEA and U.S. industrial sites",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round2/industrial_facilities_round2.tsv":
          "Canada and Australia industrial sites",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round3/industrial_facilities_round3.tsv":
          "United Kingdom industrial sites",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round4/industrial_facilities_round4.tsv":
          "Switzerland industrial sites",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round5/industrial_facilities_round5.tsv":
          "UK anaerobic digestion and France hydrogen sites",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round6/industrial_facilities_round6.tsv":
          "Brazil biofuels and U.S. landfill-gas projects",
        "05_global_reactor_map/imports/industrial_facilities/expansion_round7/industrial_facilities_round7.tsv":
          "Swiss and Italian biogas sites",
      };
      return Object.hasOwn(labels, path) ? labels[path] : path;
    }
    /**
     * Bind source-layer, country, status and text filters and the two complete-data exports.
     * @returns {void} Original options and records display with the native map when available.
     * @throws {Error} A required control or insertion label is unavailable.
     */
    function initFacilityMap() {
      let rows = facilityRows,
        statusLabel = elements
          .requireElement(document, "facilityStatus", "select")
          .closest("label");
      if (!document.getElementById("facilityKind")) {
        if (!statusLabel)
          throw new Error("Required Atlas filter label is unavailable");
        statusLabel.insertAdjacentHTML(
          "beforebegin",
          '<label>Layer<select id="facilityKind"><option value="all">All record layers</option></select></label><label>Dataset<select id="facilityDataset"><option value="all">All source datasets</option></select></label><label>Country<select id="facilityCountry"><option value="all">All countries</option></select></label>',
        );
      }
      if (!document.getElementById("facilityExportCsv")) {
        elements
          .requireElement(document, "facilityCompleteness", "span")
          .insertAdjacentHTML(
            "beforebegin",
            '<button id="facilityExportCsv" class="data-export" type="button">Export filtered CSV</button><button id="facilityExportJson" class="data-export" type="button">Export filtered JSON</button>',
          );
        elements
          .requireElement(document, "facilityCompleteness", "span")
          .insertAdjacentHTML(
            "afterend",
            '<span id="facilityLayerSummary" class="layer-summary"></span>',
          );
        elements.requireElement(
          document,
          "facilityExportCsv",
          "button",
        ).onclick =
          /**
           * Download current filtered rows using the original CSV columns.
           * @returns {void} Native CSV download retains the selected source records.
           */
          () => downloadFacilityData("csv");
        elements.requireElement(
          document,
          "facilityExportJson",
          "button",
        ).onclick =
          /**
           * Download current filtered rows with every original JSON cell.
           * @returns {void} Native JSON download retains the complete selected records.
           */
          () => downloadFacilityData("json");
      }
      [
        ["facilityDomain", "domain"],
        ["facilityKind", "record_kind"],
        ["facilityCountry", "country"],
        ["facilityStatus", "status"],
      ].forEach(([id, k]) =>
        [...new Set(rows.map((x) => x[k]).filter(Boolean))]
          .sort()
          .forEach((v) =>
            elements
              .requireElement(document, id, "select")
              .insertAdjacentHTML("beforeend", `<option>${esc(v)}</option>`),
          ),
      );
      [
        ...new Set(
          rows
            .map((x) => x.dataset_source)
            .filter((value) => value !== undefined)
            .filter(Boolean),
        ),
      ]
        .sort((a, b) =>
          facilityDatasetLabel(a).localeCompare(facilityDatasetLabel(b)),
        )
        .forEach((value) =>
          elements
            .requireElement(document, "facilityDataset", "select")
            .insertAdjacentHTML(
              "beforeend",
              `<option value="${esc(value)}">${esc(facilityDatasetLabel(value))}</option>`,
            ),
        );
      [
        "facilityDomain",
        "facilityKind",
        "facilityDataset",
        "facilityCountry",
        "facilityStatus",
        "facilitySearch",
      ].forEach((id) =>
        elements
          .requireElement(
            document,
            id,
            id === "facilitySearch" ? "input" : "select",
          )
          .addEventListener(
            id === "facilitySearch" ? "input" : "change",
            renderFacilities,
          ),
      );
      elements.requireSelector(
        document,
        "#global-map .section-head p",
        "p",
      ).textContent =
        "Explore sourced power-reactor units, research reactors, fusion devices, anaerobic digesters and reported chemical/food industrial sites. A site record does not prove an individual reactor vessel; inspect each record's caveat.";
      initMapEngine();
      renderFacilities();
    }
    /**
     * Create the canvas map engine, replacing the former SVG point layer.
     *
     * The coastline is recovered from the bundled basemap path, so switching
     * projection reuses the bundled geometry. Natural Earth borders share that viewport.
     * @returns {void} The native map is mounted or its original optional-basemap status is shown.
     */
    function initMapEngine() {
      const host = document.getElementById("mapHost");
      const namespace = window.AtlasMap;
      const Engine = namespace?.MapEngine;
      const coastline = namespace?.coastline;
      if (!host || !Engine || !coastline || !namespace.renderer || atlasMap)
        return;
      let rings;
      let borders;
      try {
        rings = coastline.fromDocument(document, "#worldMap path.land");
        borders = namespace.renderer.countryBorders(
          window.ATLAS_COUNTRY_BOUNDARIES,
        );
      } catch {
        // A missing basemap must not take the rest of the section down with it.
        host.textContent =
          "Basemap geometry unavailable; records remain listed below.";
        return;
      }
      const mounted = new Engine({
        container: host,
        document: document,
        rings: rings,
        borders: borders,
        projection: "equal-earth",
        /**
         * Open the unchanged original facility emitted by native map selection.
         * @param {import("./application-data.js").ApplicationFacility} row Actual admitted dataset row retained by the engine.
         * @returns {void} Original facility details are displayed.
         */
        onSelect: (row) => openFacility(row.id),
        /**
         * Report the native map's current record groups and viewport zoom.
         * @param {import("./map/engine.js").ViewReport} view Just-painted record counts and CSS-pixel viewport state.
         * @returns {void} Optional map summary reflects this view without physical-operation claims.
         */
        onViewChange: (view) => {
          const el = document.getElementById("mapViewSummary");
          if (el) {
            el.textContent =
              view.mapped.toLocaleString("en-GB") +
              " mapped · " +
              view.clusters.toLocaleString("en-GB") +
              " groups in view · zoom " +
              view.zoom.toFixed(1) +
              "×";
          }
        },
      });
      atlasMap = mounted;
      mounted.resize();
      window.addEventListener("resize", () => mounted.resize());
    }
    /**
     * Select facilities by current domain, layer, dataset, country, status and text.
     * @returns {import("./application-data.js").ApplicationFacility[]} Matching original rows in source order, with all extra cells retained.
     */
    function filteredFacilities() {
      let all = facilityRows,
        d = elements.requireElement(document, "facilityDomain", "select").value,
        k = elements.requireElement(document, "facilityKind", "select").value,
        dataset = elements.requireElement(
          document,
          "facilityDataset",
          "select",
        ).value,
        c = elements.requireElement(
          document,
          "facilityCountry",
          "select",
        ).value,
        s = elements.requireElement(document, "facilityStatus", "select").value,
        q = elements
          .requireElement(document, "facilitySearch", "input")
          .value.toLowerCase();
      return all.filter(
        (x) =>
          (d === "all" || x.domain === d) &&
          (k === "all" || x.record_kind === k) &&
          (dataset === "all" || x.dataset_source === dataset) &&
          (c === "all" || x.country === c) &&
          (s === "all" || x.status === s) &&
          `${x.name} ${x.country} ${x.type} ${x.operator || x.organization || ""} ${x.purpose || ""} ${x.process_or_activity || ""} ${x.fuel_or_feed || ""}`
            .toLowerCase()
            .includes(q),
      );
    }
    /**
     * Download complete current filtered records through their original CSV/JSON representation.
     * @param {string} format Actual export-control format.
     * @returns {void} A native Blob download retains original source cells and array representations.
     */
    function downloadFacilityData(format) {
      const payload = globalThis.AtlasFacilityExport.serialize(
        filteredFacilities(),
        format,
      );
      const blob = new Blob([payload], {
          type: format === "json" ? "application/json" : "text/csv",
        }),
        link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `reactor-atlas-filtered-${new Date().toISOString().slice(0, 10)}.${format}`;
      link.click();
      URL.revokeObjectURL(link.href);
    }
    /**
     * Map every matching source record and cap only its visible list at 250 cards.
     * @returns {void} Full filtered counts, source-layer totals and original card selections display.
     */
    function renderFacilities() {
      let all = facilityRows,
        rows = filteredFacilities(),
        visible = rows.slice(0, 250);
      if (atlasMap) {
        atlasMap.setData(rows);
      }
      elements.requireElement(document, "facilityList", "aside").innerHTML =
        (rows.length > 250
          ? '<p class="list-limit">Showing the first 250 matching records. Refine the filters or search to inspect the remainder.</p>'
          : "") +
          visible
            .map(
              (x) =>
                `<article><span>${esc(x.country)} · ${esc(x.status)} · ${esc(x.record_kind || "facility")}</span><h3><button class="facility-open" data-id="${esc(x.id)}">${esc(x.name)}</button></h3><p>${esc(x.type)}</p><a href="${safeUrl(x.source_url)}" target="_blank" rel="noopener">source ↗</a></article>`,
            )
            .join("") || "<p>No matching facilities.</p>";
      elements
        .requireElements(document, ".facility-open[data-id]", "button")
        .forEach((el) => {
          /**
           * Open the unchanged identity carried by this generated facility button.
           * @returns {void} Source details render or the absent record remains unopened.
           */
          el.onclick = () => openFacility(el.dataset.id);
        });
      let mapped = rows.filter((x) => x.lon !== null && x.lat !== null).length;
      elements.requireElement(
        document,
        "facilityCompleteness",
        "span",
      ).textContent =
        `${rows.length} of ${all.length} records · ${mapped} mapped · list capped at 250 · current status may be unverified`;
      /** @type {Map<string, number>} */
      const counts = new Map();
      for (const row of rows)
        counts.set(row.domain, (counts.get(row.domain) || 0) + 1);
      const domainCounts = [...counts];
      elements.requireElement(
        document,
        "facilityLayerSummary",
        "span",
      ).textContent = domainCounts
        .map(([domain, count]) => `${domain}: ${count}`)
        .join(" · ");
    }
    return Object.freeze({
      start: initFacilityMap,
      filtered: filteredFacilities,
      download: downloadFacilityData,
      open: openFacility,
      /**
       * Return the original native instance mounted by this owner.
       * @returns {import("./browser-contracts.js").AtlasFacilityMap|null} The actual mounted instance, or explicit absence.
       */
      get map() {
        return atlasMap;
      },
    });
  }
  return Object.freeze({ create });
})();
globalThis.AtlasFacilityCatalogue = AtlasFacilityCatalogue;
