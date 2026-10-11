// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — original authored taxonomy tuple construction and parent binding.
"use strict";

/**
 * Explicit stable identities and source/scope/date overrides; absence retains authored defaults.
 * @typedef {{id?:string,parent_id?:string|null,source?:string,evidence_scope?:string,reviewed_on?:string}} TaxonomyOverrides
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
    /** @type {Set<string>} Constructed catalogue identities. */
    const identities = new Set();
    /** @type {Map<string,string|null>} Explicit parent identities independent of captions. */
    const declaredParents = new Map();
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
     * @throws {Error} A source locator or stable identity is invalid or duplicated.
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
        const id = Object.hasOwn(overrides, "id")
          ? overrides.id
          : name
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, "-")
              .replace(/^-|-$/g, "");
        if (typeof id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))
          throw new Error("Taxonomy stable identity is invalid");
        if (identities.has(id)) throw new Error("Duplicate ID");
        const explicitParent = Object.hasOwn(overrides, "parent_id");
        const parentId = overrides.parent_id;
        if (
          explicitParent &&
          parentId !== null &&
          (typeof parentId !== "string" ||
            !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(parentId))
        )
          throw new Error("Taxonomy parent identity is invalid");
        const entrySource = overrides.source || source;
        const sourceIds = entrySource.split(" ");
        const sourceUrls = sourceIds.map(sourceUrl);
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
          source_ids: sourceIds,
          source_urls: sourceUrls,
          evidence_scope: overrides.evidence_scope || defaultScope,
          reviewed_on: overrides.reviewed_on || "2026-09-26",
          parent_id: null,
          source_audit:
            "Introductory reference mapping; per-claim source audit pending",
        });
        identities.add(id);
        if (explicitParent && parentId !== undefined)
          declaredParents.set(id, parentId);
      }
    }
    /**
     * Link parents only after every original authored entry has been constructed.
     * @returns {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} Original rows in insertion order, retaining missing parent identities as null.
     * @throws {Error} An explicit parent identity has no catalogue entry.
     */
    function complete() {
      for (const parentId of declaredParents.values())
        if (parentId !== null && !identities.has(parentId))
          throw new Error("Missing parent");
      for (const row of rows) {
        const explicitParent = declaredParents.get(row.id);
        if (explicitParent !== undefined) row.parent_id = explicitParent;
        else {
          const parent = rows.find(
            (candidate) => candidate.name === row.parent,
          );
          row.parent_id = parent ? parent.id : null;
        }
      }
      return rows;
    }
    return Object.freeze({ add, complete });
  }
  return Object.freeze({ create });
})();

globalThis.AtlasTaxonomyConstruction = AtlasTaxonomyConstruction;
if (typeof module !== "undefined") module.exports = AtlasTaxonomyConstruction;
