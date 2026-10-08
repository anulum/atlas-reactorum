// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — admission of original dataset cells consumed by the application.
"use strict";

/**
 * Original source-field observation; source binding remains owned by its producer.
 * @typedef {object} ApplicationFieldObservation
 * @property {string} target_id Original target identity.
 * @property {string} target_dataset Original target table.
 * @property {string} target_sha256 Original target digest.
 * @property {string} field Original displayed field.
 * @property {string} value Original published cell.
 * @property {string} basis Original classification meaning.
 * @property {string} source_record_id Original source record identity.
 * @property {string} source_field Original source column.
 * @property {string} source_artifact Original source artifact.
 * @property {string} source_sha256 Original source digest.
 * @property {string} source_url Original source locator.
 * @property {string} checked Original capture date.
 * @property {string} license Original source rights.
 */
/**
 * Admitted facility display/filter cells; unconsumed producer cells remain unknown.
 * @typedef {Record<string, unknown> & {
 * id:string,name:string,country:string,domain:string,type:string,status:string,
 * evidence:string,completeness:string,source_url:string,lat:number|null,lon:number|null,
 * record_kind?:string,dataset_source?:string,source_urls?:string[],
 * field_observations?:ApplicationFieldObservation[]
 * }} ApplicationFacility
 */
/**
 * Admitted company filter and source cells, retaining all original extra fields.
 * @typedef {Record<string, unknown> & {
 * name:string,country:string,approach:string,status:string,evidence:string,
 * company_claim:string,independent_evidence:string,source_url:string,
 * independent_source_url?:string,source_urls?:string[]
 * }} ApplicationCompany
 */
/**
 * Original repository-card fields, without technical capability admission.
 * @typedef {Record<string, unknown> & {
 * name:string,description:string,category:string,url:string,updated_at:string,
 * license:string,topics:string[]
 * }} ApplicationRepository
 */

/** Dataset shape admission shared by the actual browser and native consumers. */
var AtlasApplicationData = (() => {
  /**
   * Require a record object without changing its original properties or prototype.
   * @param {unknown} value Original input row or dataset document.
   * @returns {Record<string, unknown>} Original object after shape admission.
   * @throws {Error} The input is absent, primitive or an array.
   */
  function mapping(value) {
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error("Atlas dataset record must be an object");
    return /** @type {Record<string, unknown>} */ (value);
  }
  /**
   * Retain a legacy array or actual generated wrapper without copying source cells.
   * @param {unknown} value Original generated dataset or explicit absence.
   * @returns {unknown[]} Original records; absent datasets retain an empty collection.
   * @throws {Error} A present collection or declared record count is malformed.
   */
  function records(value) {
    if (value === undefined || value === null) return [];
    if (Array.isArray(value)) return /** @type {unknown[]} */ (value);
    const document = mapping(value);
    if (!Object.hasOwn(document, "records") || !Array.isArray(document.records))
      throw new Error("Atlas dataset records must be an array");
    if (
      document.record_count !== undefined &&
      (!Number.isInteger(document.record_count) ||
        document.record_count !== document.records.length)
    )
      throw new Error("Atlas dataset record count differs");
    return /** @type {unknown[]} */ (document.records);
  }
  /**
   * Admit required and optional textual cells actually consumed by the caller.
   * @param {Record<string, unknown>} row Original record object.
   * @param {readonly string[]} required Original required text field identities.
   * @param {readonly string[]} optional Optional consumed text field identities.
   * @returns {void} Every admitted text cell retains its original value.
   * @throws {Error} A required cell is absent/inherited or a present text cell is malformed.
   */
  function textCells(row, required, optional) {
    for (const key of required) {
      if (!Object.hasOwn(row, key) || typeof row[key] !== "string")
        throw new Error("Atlas dataset text cell is unavailable: " + key);
    }
    for (const key of optional) {
      if (row[key] !== undefined && typeof row[key] !== "string")
        throw new Error("Atlas dataset text cell is unavailable: " + key);
    }
  }
  /**
   * Require original textual array cells before callers access references or topics.
   * @param {unknown} value Original array before element admission.
   * @returns {void} The original array contains only text cells.
   * @throws {Error} The array or one of its cells is malformed.
   */
  function textArray(value) {
    if (!Array.isArray(value))
      throw new Error("Atlas dataset text array is unavailable");
    for (const cell of /** @type {unknown[]} */ (value)) {
      if (typeof cell !== "string")
        throw new Error("Atlas dataset text array is unavailable");
    }
  }
  /**
   * Admit original optional source URL lists without replacing missing locators.
   * @param {Record<string, unknown>} row Actual original source row.
   * @returns {void} Present source arrays retain their original textual cells.
   * @throws {Error} A present source list is malformed.
   */
  function sourceLists(row) {
    if (row.source_urls !== undefined) textArray(row.source_urls);
  }
  /**
   * Admit facility fields used by native map coordinates, filters and source details.
   * @param {unknown} input Original generated wrapper or legacy array.
   * @returns {ApplicationFacility[]} Original admitted rows with unknown extra cells retained.
   * @throws {Error} A consumed cell, coordinate or source observation is malformed.
   */
  function facilities(input) {
    const actual = records(input);
    for (const value of actual) {
      const row = mapping(value);
      textCells(
        row,
        [
          "id",
          "name",
          "country",
          "domain",
          "type",
          "status",
          "evidence",
          "completeness",
          "source_url",
        ],
        ["record_kind", "dataset_source"],
      );
      /** @type {[string, number][]} */
      const coordinates = [
        ["lat", 90],
        ["lon", 180],
      ];
      for (const [field, bound] of coordinates) {
        const coordinate = row[field];
        if (
          coordinate !== null &&
          (typeof coordinate !== "number" ||
            !Number.isFinite(coordinate) ||
            Math.abs(coordinate) > bound)
        )
          throw new Error("Atlas facility coordinate is unavailable: " + field);
      }
      sourceLists(row);
      if (row.field_observations !== undefined) {
        if (!Array.isArray(row.field_observations))
          throw new Error("Atlas facility observations must be an array");
        for (const observation of /** @type {unknown[]} */ (
          row.field_observations
        ))
          textCells(
            mapping(observation),
            [
              "target_id",
              "target_dataset",
              "target_sha256",
              "field",
              "value",
              "basis",
              "source_record_id",
              "source_field",
              "source_artifact",
              "source_sha256",
              "source_url",
              "checked",
              "license",
            ],
            [],
          );
      }
    }
    return /** @type {ApplicationFacility[]} */ (actual);
  }
  /**
   * Admit original company fields without promoting claims into independent evidence.
   * @param {unknown} input Original generated wrapper or legacy array.
   * @returns {ApplicationCompany[]} Original display records, with other source cells unknown.
   * @throws {Error} A consumed text or source-list cell is malformed.
   */
  function companies(input) {
    const actual = records(input);
    for (const value of actual) {
      const row = mapping(value);
      textCells(
        row,
        [
          "name",
          "country",
          "approach",
          "status",
          "evidence",
          "company_claim",
          "independent_evidence",
          "source_url",
        ],
        ["independent_source_url"],
      );
      sourceLists(row);
    }
    return /** @type {ApplicationCompany[]} */ (actual);
  }
  /**
   * Admit repository-card cells from the original producer document.
   * @param {unknown} input Original repository document or legacy array.
   * @returns {ApplicationRepository[]} Original source rows; no capability or control admission.
   * @throws {Error} A consumed text or topic list is malformed.
   */
  function repositories(input) {
    const actual = records(input);
    for (const value of actual) {
      const row = mapping(value);
      textCells(
        row,
        ["name", "description", "category", "url", "updated_at", "license"],
        [],
      );
      textArray(row.topics);
    }
    return /** @type {ApplicationRepository[]} */ (actual);
  }
  /**
   * Admit original historical audit text while leaving new citation cells to their owner.
   * @param {unknown} input Actual generated historical audit document or array.
   * @returns {import("./scripts/taxonomy_export_inputs.cjs").HistoricalAudit[]} Original historical fields, without present-day review claims.
   * @throws {Error} A consumed original audit cell is malformed.
   */
  function audits(input) {
    const actual = records(input);
    for (const value of actual)
      textCells(
        mapping(value),
        [
          "id",
          "name",
          "classification_ok",
          "source_directness",
          "source_access",
          "issue",
          "recommended_action",
          "verified_source_url",
          "audit_date",
        ],
        [],
      );
    return /** @type {import("./scripts/taxonomy_export_inputs.cjs").HistoricalAudit[]} */ (
      actual
    );
  }
  /**
   * Admit the complete authored taxonomy shape before source-bound consumers use it.
   * @param {unknown} input Original authored catalogue or explicit absence.
   * @returns {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} Original complete rows; absence never invents source identities.
   * @throws {Error} A text, reference, parent or scalar cell is malformed.
   */
  function taxonomy(input) {
    const actual = records(input);
    for (const value of actual) {
      const row = mapping(value);
      textCells(
        row,
        [
          "id",
          "name",
          "domain",
          "family",
          "parent",
          "kind",
          "maturity",
          "evidence",
          "principle",
          "strength",
          "challenge",
          "temp",
          "mode",
          "evidence_scope",
          "reviewed_on",
          "source_audit",
        ],
        [],
      );
      textArray(row.source_ids);
      textArray(row.source_urls);
      if (row.parent_id !== null && typeof row.parent_id !== "string")
        throw new Error("Atlas taxonomy parent identity is unavailable");
      for (const field of ["scale", "control"]) {
        const scalar = row[field];
        if (
          scalar !== null &&
          (typeof scalar !== "number" || !Number.isFinite(scalar))
        )
          throw new Error("Atlas taxonomy scalar is unavailable: " + field);
      }
    }
    return /** @type {import("./scripts/taxonomy_export_inputs.cjs").TaxonomyRow[]} */ (
      actual
    );
  }
  return Object.freeze({
    facilities,
    companies,
    repositories,
    audits,
    taxonomy,
  });
})();

globalThis.AtlasApplicationData = AtlasApplicationData;
