// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original authored taxonomy tuple construction and parent binding.
"use strict";

/**
 * Original entry-specific source/scope/date overrides; absence retains family defaults.
 * @typedef {{source?:string,evidence_scope?:string,reviewed_on?:string}} TaxonomyOverrides
 */
/**
 * Original ordered name, parent, maturity, evidence and descriptive fields.
 * @typedef {[string,string|null,string,string,string,string,string,string?,TaxonomyOverrides?]} TaxonomyDefinition
 */
/**
 * Constructor of one authored catalogue, using original source locators and row values.
 * @typedef {{add:(domain:string,family:string,source:string,definitions:TaxonomyDefinition[])=>void,complete:()=>import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]}} TaxonomyBuilder
 */

/** Same construction API for classic browser scripts and the native source readers. */
var AtlasTaxonomyConstruction = (() => {
  /**
   * Construct a catalogue against one actual authored source locator table.
   * @param {unknown} input Original source-key table, before object/string admission.
   * @returns {TaxonomyBuilder} Family construction and final parent linking without source inference.
   * @throws {Error} A source table or selected source identity/locator is unavailable.
   */
  function create(input) {
    if (!input || typeof input !== "object" || Array.isArray(input))
      throw new Error("Taxonomy source table is unavailable");
    const sources = /** @type {Record<string, unknown>} */ (input);
    /** @type {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} */
    const rows = [];
    /**
     * Resolve only an owned textual locator before constructing source reference cells.
     * @param {string} identity Original source key in an entry or family list.
     * @returns {string} Original locator without source-role or date inference.
     * @throws {Error} A source identity is unavailable, inherited or nontextual.
     */
    function sourceUrl(identity) {
      if (
        !Object.hasOwn(sources, identity) ||
        typeof sources[identity] !== "string"
      )
        throw new Error("Taxonomy source identity is unavailable");
      return sources[identity];
    }
    /**
     * Append original family entries with their explicit source/scope/date overrides.
     * @param {string} domain Original domain.
     * @param {string} family Original family description.
     * @param {string} source Original space-separated family source keys.
     * @param {TaxonomyDefinition[]} definitions Original ordered entry tuples.
     * @returns {void} Original rows append in order; numeric scores remain explicitly absent.
     * @throws {Error} A selected source locator is unavailable.
     */
    function add(domain, family, source, definitions) {
      for (const [
        name,
        parent,
        maturity,
        evidence,
        principle,
        strength,
        challenge,
        kind = "architecture",
        overrides = {},
      ] of definitions) {
        const id = name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
        const entrySource = overrides.source || source;
        const defaultScope =
          evidence === "established"
            ? "Established process or reactor architecture; individual designs require separate qualification."
            : evidence === "contested"
              ? "Claim under dispute; this listing is not validation."
              : "Evidence concerns experiments, components or analysis; it does not establish an integrated commercial power plant.";
        rows.push({
          id,
          name,
          domain,
          family,
          parent: parent || family,
          kind,
          maturity,
          evidence,
          principle,
          strength,
          challenge,
          temp: "Design and application dependent; see source",
          mode:
            domain === "fusion"
              ? "Configuration dependent; pulsed or sustained experiments"
              : "Design dependent",
          scale: null,
          control: null,
          source_ids: entrySource.split(" "),
          source_urls: entrySource.split(" ").map(sourceUrl),
          evidence_scope: overrides.evidence_scope || defaultScope,
          reviewed_on: overrides.reviewed_on || "2026-09-26",
          parent_id: null,
          source_audit:
            "Introductory reference mapping; per-claim source audit pending",
        });
      }
    }
    /**
     * Link parents only after every original authored entry has been constructed.
     * @returns {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} Original rows in insertion order, retaining missing parent identities as null.
     */
    function complete() {
      for (const row of rows) {
        const parent = rows.find((candidate) => candidate.name === row.parent);
        row.parent_id = parent ? parent.id : null;
      }
      return rows;
    }
    return Object.freeze({ add, complete });
  }
  return Object.freeze({ create });
})();

globalThis.AtlasTaxonomyConstruction = AtlasTaxonomyConstruction;
if (typeof module !== "undefined") module.exports = AtlasTaxonomyConstruction;
