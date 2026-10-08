// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — company-catalogue-controller.js
"use strict";

/** Company/project filters retaining the producer evidence boundaries. */
var AtlasCompanyCatalogue = (() => {
  /**
   * Bind company filters to retained claims, milestones, caveats and sources.
   * @param {Document} document Actual company section and controls.
   * @param {import("./application-data.js").ApplicationCompany[]} companyRows Admitted original company records; other producer cells remain unknown.
   * @returns {{start:()=>void,render:()=>void}} Initial facet population and original filtered cards.
   */
  function create(document, companyRows) {
    const elements = globalThis.AtlasBrowserElements;
    const esc = globalThis.AtlasPresentationText.escape;
    const sourceLinks = globalThis.AtlasPresentationText.sourceLinks;

    /**
     * Populate four original company facets and bind them alongside text search.
     * @returns {void} Original company values and initial evidence-screening cards are ready.
     */
    function initCompanies() {
      let rows = companyRows;
      [
        ["companyApproach", "approach"],
        ["companyCountry", "country"],
        ["companyEvidence", "evidence"],
        ["companyStatus", "status"],
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
        "companyApproach",
        "companyCountry",
        "companyEvidence",
        "companyStatus",
      ].forEach(
        (id) =>
          (elements.requireElement(document, id, "select").onchange =
            renderCompanies),
      );
      elements.requireElement(document, "companySearch", "input").oninput =
        renderCompanies;
      renderCompanies();
    }
    /**
     * Filter companies while keeping supplied claims and independent evidence separate.
     * @returns {void} Matching cards retain original milestones, caveats, dates and sources.
     */
    function renderCompanies() {
      let a = elements.requireElement(
          document,
          "companyApproach",
          "select",
        ).value,
        c = elements.requireElement(document, "companyCountry", "select").value,
        e = elements.requireElement(
          document,
          "companyEvidence",
          "select",
        ).value,
        s = elements.requireElement(document, "companyStatus", "select").value,
        q = elements
          .requireElement(document, "companySearch", "input")
          .value.toLowerCase(),
        all = companyRows,
        rows = all.filter(
          (x) =>
            (a === "all" || x.approach === a) &&
            (c === "all" || x.country === c) &&
            (e === "all" || x.evidence === e) &&
            (s === "all" || x.status === s) &&
            [
              x.name,
              x.country,
              x.approach,
              x.identity_class,
              x.public_devices_projects,
              x.company_claim,
              x.independent_evidence,
              x.unsupported_or_ambiguous_claims,
              x.notes,
            ]
              .join(" ")
              .toLowerCase()
              .includes(q),
        );
      elements.requireElement(document, "companyCount", "p").textContent =
        `${rows.length} of ${all.length} audited company/project records`;
      elements.requireElement(document, "companyGrid", "div").innerHTML =
        rows
          .map(
            (x) =>
              `<article><span class="badge">${esc(x.evidence)}</span><h3>${esc(x.name)}</h3><p class="company-meta">${esc(x.country)} · ${esc(x.approach)} · ${esc(x.status)}</p><dl>${x.identity_class ? `<dt>Identity class</dt><dd>${esc(x.identity_class)}</dd>` : ""}${x.public_devices_projects ? `<dt>Public devices / projects</dt><dd>${esc(x.public_devices_projects)}</dd>` : ""}<dt>Company claim</dt><dd>${esc(x.company_claim || "Not catalogued")}</dd><dt>Highest independently supported milestone</dt><dd>${esc(x.independent_evidence || "Not assessed")}</dd>${x.evidence_tier ? `<dt>Evidence tier</dt><dd>${esc(x.evidence_tier)}</dd>` : ""}${x.status_detail ? `<dt>Status detail</dt><dd>${esc(x.status_detail)}</dd>` : ""}${x.confidence ? `<dt>Audit confidence</dt><dd>${esc(x.confidence)}</dd>` : ""}${x.data_caveat ? `<dt>Unsupported / ambiguous claims</dt><dd>${esc(x.data_caveat)}</dd>` : ""}${x.evidence_maturity ? `<dt>Candidate evidence notes</dt><dd>${esc(x.evidence_maturity)}</dd>` : ""}${x.notes ? `<dt>Registry notes</dt><dd>${esc(x.notes)}</dd>` : ""}</dl><div class="detail-sources">${sourceLinks(x.source_urls || [x.source_url, x.independent_source_url])}</div></article>`,
          )
          .join("") || "<p>No matching companies.</p>";
    }
    return Object.freeze({ start: initCompanies, render: renderCompanies });
  }
  return Object.freeze({ create });
})();
globalThis.AtlasCompanyCatalogue = AtlasCompanyCatalogue;
