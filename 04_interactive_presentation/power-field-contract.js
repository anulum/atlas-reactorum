// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — whole power field and presentation admission
"use strict";

if (typeof require !== "undefined") require("./power-source-contract.js");

/**
 * Original author observation, without promoting a candidate into a scalar.
 * @typedef {Record<string, unknown> & {
 * basis:string,scope:string,candidate_value:string,
 * citations:import("./power-source-contract.js").PowerCitation[],capture_attempts:string[]
 * }} PowerObservation
 */
/**
 * Completed source-bound decision for one originally blank cell.
 * @typedef {Record<string, unknown> & {
 * stable_id:string,field:string,original_value:string,original_context:Record<string,string>,
 * disposition:string,value:string,role:string,basis:string,scope:string,
 * citations:import("./power-source-contract.js").PowerCitation[],observations:PowerObservation[],
 * author_review:string,independent_review:null,rights_scope:string
 * }} PowerDecision
 */
/** A citation with its original source custody resolved for standalone exports. */
/** @typedef {import("./power-source-contract.js").PowerCitation & import("./power-source-contract.js").PowerSourceRecord} PresentedPowerCitation */
/** A source-scope observation retaining refusal records separately from documents. */
/** @typedef {Record<string,unknown> & {basis:string,scope:string,candidate_value:string,citations:PresentedPowerCitation[],capture_attempts:import("./power-source-contract.js").PowerSourceRecord[]}} PresentedPowerObservation */
/** Self-contained field decision used by the actual detail and download consumers. */
/**
 * @typedef {Record<string,unknown> & {
 * stable_id:string,field:string,original_value:string,original_context:Record<string,string>,
 * disposition:string,value:string,role:string,basis:string,scope:string,
 * citations:PresentedPowerCitation[],observations:PresentedPowerObservation[],
 * author_review:string,independent_review:null,rights_scope:string
 * }} PresentedPowerDecision
 */

/** Whole original-gap admission, shared by actual browser and native consumers. */
var PowerFieldContract = (() => {
  const C = globalThis.PowerSourceContract;
  const fields = new Set(["operator", "reactor_type"]);
  const contextFields = [
    "unit_name",
    "plant_name",
    "country",
    "status",
    "lat",
    "lon",
    "model",
    "owner",
    "nameplate_mw",
    "operator",
    "reactor_type",
  ];
  const operatorRoles = new Set([
    "actual_operator",
    "historical_operator",
    "explicit_intended_operator",
    "explicit_designated_future_operator",
    "licensed_project_organisation_combined_install_and_operate",
  ]);
  const designRoles = new Set(["historical_design", "proposed_design"]);

  /**
   * Require a retained source scope with its documents or explicit failed attempts.
   * @param {unknown} input Original observation array.
   * @param {Map<string, import("./power-source-contract.js").PowerSourceRecord>} sources Complete admitted registry.
   * @returns {void} Each observation preserves its original source meaning.
   */
  function admitObservations(input, sources) {
    const observations = C.sequence(input);
    if (!observations.length)
      throw new Error("power decision requires a source-scope observation");
    for (const item of observations) {
      const row = C.mapping(item);
      C.text(row, "basis");
      C.text(row, "scope");
      C.text(row, "candidate_value", true);
      const citations = C.admitCitations(row.citations, sources, false),
        attempts = C.sequence(row.capture_attempts),
        seen = new Set();
      for (const identity of attempts) {
        if (typeof identity !== "string" || seen.has(identity))
          throw new Error(
            "power capture-attempt identity is invalid or duplicate",
          );
        const source = sources.get(identity);
        if (!source || source.body_state !== "capture_attempt")
          throw new Error(
            "power capture-attempt reference lacks an attempt record",
          );
        seen.add(identity);
      }
      if (!citations.length && !attempts.length)
        throw new Error(
          "power observation requires a document or a capture attempt",
        );
    }
  }
  /**
   * Admit an exact blank-cell decision without replacing known values or stages.
   * @param {unknown} input Original completed author decision.
   * @param {Record<string,string>} original Complete original source row.
   * @param {Map<string, import("./power-source-contract.js").PowerSourceRecord>} sources Complete admitted registry.
   * @returns {PowerDecision} Original admitted decision.
   */
  function admitDecision(input, original, sources) {
    const row = C.mapping(input),
      field = C.text(row, "field");
    if (!fields.has(field) || original[field] || row.original_value !== "")
      throw new Error(
        "power decision may only target an originally blank operator/type",
      );
    const context = C.mapping(row.original_context);
    if (
      Object.keys(context).length !== contextFields.length ||
      contextFields.some((key) => context[key] !== original[key])
    )
      throw new Error("power decision context differs from the original unit");
    const disposition = C.text(row, "disposition"),
      selected = disposition === "qualified",
      scalar = C.text(row, "value", true),
      role = C.text(row, "role", true);
    if (!["qualified", "held", "unknown"].includes(disposition))
      throw new Error("power decision is not a completed author disposition");
    if (selected) {
      const permitted = field === "operator" ? operatorRoles : designRoles;
      if (!scalar.trim() || !permitted.has(role))
        throw new Error(
          "selected power value requires an explicit qualified field role",
        );
    } else if (scalar || role)
      throw new Error(
        "held/unknown power decisions cannot fill a scalar or assign a role",
      );
    C.text(row, "basis");
    C.text(row, "scope");
    const citations = C.admitCitations(row.citations, sources, selected);
    if (!selected && citations.length)
      throw new Error(
        "held/unknown power citations belong to observations, not selected claims",
      );
    if (
      row.author_review !== "completed" ||
      !Object.hasOwn(row, "independent_review")
    )
      throw new Error(
        "power author review must be completed and separate from independent review",
      );
    if (row.independent_review !== null)
      throw new Error(
        "power projection cannot infer an independent acceptance verdict",
      );
    if (row.rights_scope !== "citation_and_factual_metadata_only")
      throw new Error(
        "power field rights must exclude original body redistribution",
      );
    admitObservations(row.observations, sources);
    return /** @type {PowerDecision} */ (row);
  }
  /**
   * Reconstruct every original row and require the complete original blank target set.
   * @param {unknown} baseline Complete original string-valued source rows.
   * @param {unknown} ledger Whole author field decisions.
   * @param {unknown} sourceRecords Original documentary custody and attempt metadata.
   * @returns {{rows:Record<string,string>[],decisions:PowerDecision[],source_records:import("./power-source-contract.js").PowerSourceRecord[]}} Complete original-order projection.
   */
  function project(baseline, ledger, sourceRecords) {
    const originalRows = C.sequence(baseline);
    if (!originalRows.length)
      throw new Error("power projection requires original rows");
    /** @type {Map<string,Record<string,string>>} */
    const originals = new Map(),
      projected = new Map();
    const expected = new Set();
    for (const item of originalRows) {
      const row = C.mapping(item),
        required = ["stable_id", ...contextFields];
      if (
        required.some((key) => !Object.hasOwn(row, key)) ||
        Object.values(row).some((cell) => typeof cell !== "string")
      )
        throw new Error(
          "power original row must retain all string-valued source cells",
        );
      const original = /** @type {Record<string,string>} */ (row),
        identity = original.stable_id;
      if (!identity || originals.has(identity))
        throw new Error("power original identity is empty or duplicate");
      originals.set(identity, original);
      projected.set(identity, { ...original });
      for (const field of fields)
        if (!original[field]) expected.add(JSON.stringify([identity, field]));
    }
    const sources = C.admitSources(sourceRecords),
      seen = new Set();
    /** @type {PowerDecision[]} */
    const decisions = [];
    for (const item of C.sequence(ledger)) {
      const row = C.mapping(item),
        identity = C.text(row, "stable_id"),
        field = C.text(row, "field"),
        key = JSON.stringify([identity, field]);
      const original = originals.get(identity),
        target = projected.get(identity);
      if (!expected.has(key) || seen.has(key) || !original || !target)
        throw new Error(
          "power ledger has an extra, known-field or duplicate target",
        );
      const decision = admitDecision(row, original, sources);
      seen.add(key);
      decisions.push(decision);
      if (decision.disposition === "qualified") target[field] = decision.value;
    }
    if (seen.size !== expected.size)
      throw new Error("power ledger omits original blank target fields");
    return {
      rows: [...projected.values()],
      decisions,
      source_records: [...sources.values()],
    };
  }
  /**
   * Admit resolved producer decisions before real browser details or downloads use them.
   * @param {unknown} input Self-contained producer decisions for one original unit.
   * @param {Record<string,unknown>} actual Actual facility row with original source stage.
   * @returns {PresentedPowerDecision[]} Original admitted presentation decisions.
   */
  function admitPresentation(input, actual) {
    const rows = C.sequence(input);
    if (!rows.length)
      throw new Error("power presentation decisions cannot be empty");
    const first = C.mapping(rows[0]),
      context = C.mapping(first.original_context);
    /** @type {Record<string,string>} */
    const original = { stable_id: C.text(actual, "stable_id") };
    for (const key of contextFields) original[key] = C.text(context, key, true);
    for (const key of contextFields) {
      if (key === "operator" || key === "reactor_type") continue;
      const value =
        key === "status"
          ? actual.source_status
          : key === "country"
            ? (actual.source_country ?? actual.country)
            : actual[key];
      if (key === "lat" || key === "lon") {
        if (
          !original[key].trim() ||
          !Number.isFinite(Number(original[key])) ||
          Number(original[key]) !== value
        )
          throw new Error(
            "power displayed coordinates differ from the original unit",
          );
      } else if (original[key] !== value)
        throw new Error(
          "power displayed source context differs from the original unit",
        );
    }
    const sourceKeys = [
      "source_id",
      "url",
      "requested_url",
      "captured_at",
      "body_sha256",
      "body_bytes",
      "http_status",
      "body_complete",
      "native_class",
      "body_state",
      "eligible_for_selection",
      "rights_scope",
    ];
    /** @type {Map<string,Record<string,unknown>>} */
    const sources = new Map();
    /**
     * Bind each resolved citation/attempt to one consistent custody identity.
     * @param {unknown} item Resolved source record or documentary citation.
     * @returns {string} Exact original source identity.
     */
    function bind(item) {
      const row = C.mapping(item),
        identity = C.text(row, "source_id"),
        record = Object.fromEntries(sourceKeys.map((key) => [key, row[key]])),
        prior = sources.get(identity);
      if (prior && JSON.stringify(prior) !== JSON.stringify(record))
        throw new Error(
          "power resolved source identity has inconsistent custody",
        );
      sources.set(identity, record);
      return identity;
    }
    const ledger = rows.map((item) => {
      const row = C.mapping(item);
      for (const citation of C.sequence(row.citations)) bind(citation);
      return {
        ...row,
        observations: C.sequence(row.observations).map((item) => {
          const observation = C.mapping(item);
          for (const citation of C.sequence(observation.citations))
            bind(citation);
          return {
            ...observation,
            capture_attempts: C.sequence(observation.capture_attempts).map(
              bind,
            ),
          };
        }),
      };
    });
    const projection = project([original], ledger, [...sources.values()]);
    for (const field of fields)
      if (projection.rows[0][field] !== C.text(actual, field, true))
        throw new Error(
          "power displayed field differs from its source-bound decision",
        );
    return /** @type {PresentedPowerDecision[]} */ (rows);
  }
  return Object.freeze({ project, admitPresentation });
})();
globalThis.PowerFieldContract = PowerFieldContract;
if (typeof module !== "undefined") module.exports = PowerFieldContract;
