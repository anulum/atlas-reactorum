// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — taxonomy-catalogue-controller.js
"use strict";

/**
 * Original display row with its optional separate historical audit.
 * @typedef {import("./browser-contracts.js").AtlasFallbackTaxonomyRow & {taxonomy_audit?:ReturnType<typeof globalThis.AtlasApplicationData.audits>[number]}} CatalogueTaxonomyRow
 */
/** Actual taxonomy facets, source cards and detail navigation. */
var AtlasTaxonomyCatalogue = (() => {
  /**
   * Create browsing controls and original details for one admitted catalogue.
   * @param {Document} document Actual Atlas document containing the controls and dialog.
   * @param {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} taxonomyRows Complete admitted original source rows.
   * @param {ReturnType<typeof globalThis.AtlasApplicationData.audits>} taxonomyAuditRows Original admitted audit records.
   * @returns {{rows:CatalogueTaxonomyRow[],start:()=>void,open:(name:string|undefined)=>void}} Original source or unattributed fallback cards and their actual controls.
   */
  function create(document, taxonomyRows, taxonomyAuditRows) {
    const fallbackReactors = globalThis.AtlasFallbackTaxonomy;
    const taxonomyAuditById = Object.fromEntries(
      taxonomyAuditRows.map((row) => [row.id, row]),
    );
    const reactors = (
      taxonomyRows.length ? taxonomyRows : fallbackReactors
    ).map((row) => ({
      ...row,
      taxonomy_audit:
        row.id === undefined ? undefined : taxonomyAuditById[row.id],
    }));
    const domainLabels = new Map(
      Object.entries({
        all: "All",
        fission: "Nuclear fission",
        fusion: "Plasma fusion",
        chemical: "Chemical / bio",
        hybrid: "Hybrid / emerging",
      }),
    );
    const maturityLabels = new Map(
      Object.entries({
        deployed: "industrial deployment",
        demonstrated: "experimental demonstration",
        research: "active research",
        contested: "contested",
        concept: "concept",
      }),
    );
    const evidenceLabels = new Map(
      Object.entries({
        established: "established",
        demonstrated: "demonstrated",
        research: "research",
        contested: "contested",
        concept: "concept",
      }),
    );
    const elements = globalThis.AtlasBrowserElements;
    const esc = globalThis.AtlasPresentationText.escape;
    const sourceLinks = globalThis.AtlasPresentationText.sourceLinks;
    let activeDomain = "all";
    /**
     * Populate taxonomy kinds and domain controls, then bind the four existing filters.
     * @returns {void} Original catalogue facets and the initial card view are ready.
     * @throws {Error} A required filter or its containing label is unavailable.
     */
    function initFilters() {
      let maturityLabel = elements
        .requireElement(document, "maturityFilter", "select")
        .closest("label");
      if (!maturityLabel)
        throw new Error("Required Atlas filter label is unavailable");
      maturityLabel.insertAdjacentHTML(
        "beforebegin",
        '<label class="select-wrap">Entry kind<select id="kindFilter"><option value="all">All kinds</option></select></label>',
      );
      [...new Set(reactors.map((r) => r.kind).filter(Boolean))]
        .sort()
        .forEach((v) =>
          elements
            .requireElement(document, "kindFilter", "select")
            .insertAdjacentHTML("beforeend", `<option>${esc(v)}</option>`),
        );
      [...domainLabels].forEach(([key, label]) => {
        let b = document.createElement("button");
        b.className = "chip" + (key === "all" ? " active" : "");
        b.textContent = label;
        /** Select this chip's domain and rebuild its dependent family choices. */
        b.onclick = () => {
          elements
            .requireElements(document, "#domainFilters .chip", "button")
            .forEach((x) => x.classList.remove("active"));
          b.classList.add("active");
          activeDomain = key;
          updateFamilies();
          renderReactors();
        };
        elements.requireElement(document, "domainFilters", "div").append(b);
      });
      elements.requireElement(document, "reactorSearch", "input").oninput =
        renderReactors;
      elements.requireElement(document, "maturityFilter", "select").onchange =
        renderReactors;
      elements.requireElement(document, "familyFilter", "select").onchange =
        renderReactors;
      elements.requireElement(document, "kindFilter", "select").onchange =
        renderReactors;
      updateFamilies();
      renderReactors();
    }
    /**
     * Rebuild family choices from records in the currently selected domain.
     * @returns {void} Original family values remain sorted without inferred categories.
     */
    function updateFamilies() {
      let options = [
        ...new Set(
          reactors
            .filter((r) => activeDomain === "all" || r.domain === activeDomain)
            .map((r) => r.family),
        ),
      ].sort();
      elements.requireElement(document, "familyFilter", "select").innerHTML =
        '<option value="all">All families</option>' +
        options.map((v) => `<option>${esc(v)}</option>`).join("");
    }
    /**
     * Apply name, maturity, family and kind filters to the original taxonomy cards.
     * @returns {void} Counts and cards retain the source or explicitly unattributed fallback rows.
     */
    function renderReactors() {
      let q = elements
          .requireElement(document, "reactorSearch", "input")
          .value.toLowerCase(),
        m = elements.requireElement(document, "maturityFilter", "select").value,
        f = elements.requireElement(document, "familyFilter", "select").value,
        k = elements.requireElement(document, "kindFilter", "select").value,
        rows = reactors.filter(
          (r) =>
            (activeDomain === "all" || r.domain === activeDomain) &&
            (m === "all" || r.maturity === m) &&
            (f === "all" || r.family === f) &&
            (k === "all" || r.kind === k) &&
            `${r.name} ${r.family} ${r.parent || ""} ${r.kind || ""} ${r.principle} ${r.taxonomy_audit?.classification_ok || ""}`
              .toLowerCase()
              .includes(q),
        );
      elements.requireElement(document, "resultCount", "strong").textContent =
        String(rows.length);
      elements.requireElement(
        document,
        "activeFilterText",
        "span",
      ).textContent =
        `of ${reactors.length} taxonomy entries · ${activeDomain === "all" ? "all domains" : domainLabels.get(activeDomain)}`;
      elements.requireElement(document, "reactorGrid", "div").innerHTML =
        rows
          .map(
            (r) =>
              `<button class="reactor-card" data-name="${esc(r.name)}"><span class="domain"><i class="dot ${esc(r.domain)}"></i>${esc(domainLabels.get(r.domain) || r.domain)} · ${esc(r.family)}</span><h3>${esc(r.name)}</h3><p>${esc(r.principle)}</p><footer><span class="maturity">${esc(r.kind || "entry")} · ${esc(maturityLabels.get(r.maturity) || r.maturity)}</span><span>↗</span></footer></button>`,
          )
          .join("") || "<p>No matching systems.</p>";
      elements
        .requireElements(document, ".reactor-card", "button")
        .forEach((b) => {
          /**
           * Open this card's original display name without creating a source identity.
           * @returns {void} Original details render or the absent selection is left unopened.
           */
          b.onclick = () => openReactor(b.dataset.name);
        });
    }
    /**
     * Open the selected original taxonomy or explicitly unattributed fallback detail.
     * @param {string|undefined} n Actual displayed name selected by its original card.
     * @returns {void} Original details retain their sources; absent source identity gets no evidence profile.
     */
    function openReactor(n) {
      let r = reactors.find((x) => x.name === n);
      if (!r) return;
      const parent = r.parent || r.family;
      const original = taxonomyRows.find((row) => row.name === n);
      const profile = original
        ? globalThis.AtlasTaxonomyEvidenceProfiles.render(
            window.REACTOR_TAXONOMY_EVIDENCE_PROFILES,
            window.REACTOR_TAXONOMY_EVIDENCE_PROFILES.inputs.taxonomy_sha256,
            original,
          )
        : '<p role="status">Source-bound evidence is unavailable for this authored fallback entry.</p>';
      elements.requireElement(document, "dialogBody", "div").innerHTML =
        `<div class="dialog-body"><span class="kicker">${esc(domainLabels.get(r.domain) || r.domain)} / ${esc(r.family)}</span><h2 id="dialogTitle">${esc(r.name)}</h2><p class="hierarchy">${esc(parent)} → ${esc(r.name)}${r.kind ? " · " + esc(r.kind) : ""}</p><div class="dialog-meta"><span>${esc(maturityLabels.get(r.maturity) || r.maturity)}</span><span>evidence: ${esc(evidenceLabels.get(r.evidence) || r.evidence)}</span></div><p class="principle">${esc(r.principle)}</p><dl>${[
          ["Strength", r.strength],
          ["Critical challenge", r.challenge],
          ["Temperature", r.temp],
          ["Operating mode", r.mode],
          [
            "Evidence scope",
            r.evidence_scope ||
              "See source material for the scope of each claim.",
          ],
          [
            "Taxonomy audit",
            r.taxonomy_audit
              ? `${r.taxonomy_audit.classification_ok}. ${r.taxonomy_audit.source_directness}`
              : "Not yet audited.",
          ],
        ]
          .map(
            ([k, v]) =>
              `<div><dt>${esc(k)}</dt><dd>${esc(v || "Not specified")}</dd></div>`,
          )
          .join(
            "",
          )}</dl>${profile}<h3>Sources</h3><div class="detail-sources">${sourceLinks(r.source_urls) || "Source mapping pending."}</div></div>`;
      elements.requireElement(document, "reactorDialog", "dialog").showModal();
    }
    return Object.freeze({
      rows: reactors,
      start: initFilters,
      open: openReactor,
    });
  }
  return Object.freeze({ create });
})();
globalThis.AtlasTaxonomyCatalogue = AtlasTaxonomyCatalogue;
